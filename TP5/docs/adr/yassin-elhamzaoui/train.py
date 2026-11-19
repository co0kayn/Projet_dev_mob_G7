"""Entraîne le modèle, le compare à la baseline, sauvegarde les artefacts et enregistre le run dans MLflow.

Usage : python -m maintai.train
        python -m maintai.train --model forest
        python -m maintai.train --C 0.1 --threshold 0.2
        python -m maintai.train --grid          (grid search : au plus 25 entraînements)
"""
import argparse
import json
import sys
from datetime import datetime, timezone

import joblib
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from maintai.config import FEATURES, SEED, TARGET, Settings, get_settings
from maintai.data import load_data, split
from maintai.tracking import log_run

# Grid search : 4 valeurs de C x 4 seuils (logreg) + 4 seuils (forest) = 20 entraînements
GRID_C = [0.01, 0.1, 1.0, 10.0]
GRID_THRESHOLDS = [0.15, 0.2, 0.25, 0.3]
MAX_RUNS = 25          # jamais plus de 25 entraînements
MIN_PRECISION = 0.5    # au moins une alerte sur deux doit être justifiée


def build_model(kind: str = "logreg", C: float = 1.0) -> Pipeline:
    """Le prétraitement fait partie du modèle : scaler et classifieur sont sauvegardés ensemble."""
    if kind == "forest":
        clf = RandomForestClassifier(n_estimators=200, random_state=SEED)
    else:
        clf = LogisticRegression(C=C, max_iter=1000)
    return Pipeline([("scale", StandardScaler()), ("clf", clf)])


def evaluate(model, X_test, y_test, threshold: float) -> dict:
    """Mesure le modèle au seuil de décision choisi, et non au seuil 0,5 par défaut."""
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= threshold).astype(int)
    return {
        "accuracy": round(float(accuracy_score(y_test, pred)), 3),
        "recall": round(float(recall_score(y_test, pred)), 3),
        "precision": round(float(precision_score(y_test, pred, zero_division=0)), 3),
        "threshold": threshold,
    }


def evaluate_baseline(X_train, y_train, X_test, y_test) -> dict:
    """La méthode la plus simple : toujours prédire la classe majoritaire (« pas de panne »)."""
    baseline = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
    pred = baseline.predict(X_test)
    return {
        "accuracy": round(float(accuracy_score(y_test, pred)), 3),
        "recall": round(float(recall_score(y_test, pred, zero_division=0)), 3),
    }


def save(model, metrics: dict, settings: Settings, threshold: float) -> None:
    """Écrit le modèle, son contrat d'entrée (model_info.json) et ses métriques."""
    settings.models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, settings.model_path)
    info = {
        "features": FEATURES,
        "target": TARGET,
        "threshold": threshold,
        "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sklearn_version": sklearn.__version__,
    }
    settings.info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")
    settings.metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m maintai.train")
    p.add_argument("--model", choices=["logreg", "forest"], default="logreg")
    p.add_argument("--C", type=float, default=1.0, help="régularisation de la régression logistique")
    p.add_argument("--threshold", type=float, default=None, help="seuil d'alerte (défaut : MAINTAI_THRESHOLD)")
    p.add_argument("--grid", action="store_true", help=f"grid search sur C et le seuil (au plus {MAX_RUNS} runs)")
    return p.parse_args(argv)


def grid_configs() -> list[tuple[str, float, float]]:
    """Les combinaisons (modèle, C, seuil) à essayer ; erreur si elles dépassent MAX_RUNS."""
    configs = [("logreg", C, t) for C in GRID_C for t in GRID_THRESHOLDS]
    configs += [("forest", 1.0, t) for t in GRID_THRESHOLDS]
    if len(configs) > MAX_RUNS:
        raise SystemExit(f"{len(configs)} entraînements prévus : la limite est {MAX_RUNS}. Réduisez la grille.")
    return configs


def train_one(kind, C, threshold, X_train, X_test, y_train, y_test, data_path, model=None):
    """Un entraînement = un run MLflow. Renvoie le modèle, ses métriques et l'id du run."""
    if model is None:
        model = build_model(kind, C).fit(X_train, y_train)
    metrics = {
        "model": evaluate(model, X_test, y_test, threshold),
        "baseline": evaluate_baseline(X_train, y_train, X_test, y_test),
        "n_train": len(X_train),
        "n_test": len(X_test),
    }
    params = {"model": kind, "threshold": threshold, "n_train": len(X_train)}
    if kind == "logreg":
        params["C"] = C
    run_id = log_run(
        params=params,
        metrics={k: v for k, v in metrics["model"].items() if k != "threshold"}
        | {"baseline_recall": metrics["baseline"]["recall"]},
        model=model,
        X_example=X_train.head(3),
        data_path=data_path,
    )
    return model, metrics, run_id


def grid_search(settings: Settings, X_train, X_test, y_train, y_test) -> dict:
    """Essaie chaque combinaison, garde le meilleur recall avec precision >= MIN_PRECISION."""
    configs = grid_configs()
    print(f"Grid search : {len(configs)} entraînements (limite : {MAX_RUNS})")
    fitted, results = {}, []
    for i, (kind, C, t) in enumerate(configs, 1):
        # Le seuil ne change pas le modèle : on l'entraîne une fois par (modèle, C)
        key = (kind, C)
        model, metrics, run_id = train_one(kind, C, t, X_train, X_test, y_train, y_test,
                                           settings.data_path, model=fitted.get(key))
        fitted[key] = model
        m = metrics["model"]
        results.append({"run_id": run_id, "kind": kind, "C": C, "threshold": t, "model": model,
                        "metrics": metrics})
        c_txt = f"C={C:<5}" if kind == "logreg" else "       "
        print(f"[{i:2}/{len(configs)}] {kind:6} {c_txt} seuil={t:<4}  recall={m['recall']:.3f}  "
              f"precision={m['precision']:.3f}  accuracy={m['accuracy']:.3f}  run={run_id[:8]}")

    ok = [r for r in results if r["metrics"]["model"]["precision"] >= MIN_PRECISION]
    if not ok:
        raise SystemExit(f"Aucun réglage n'atteint une précision de {MIN_PRECISION}.")
    best = max(ok, key=lambda r: (r["metrics"]["model"]["recall"], r["metrics"]["model"]["precision"]))
    save(best["model"], best["metrics"], settings, best["threshold"])
    m = best["metrics"]["model"]
    print(f"\nMeilleur (recall max avec precision >= {MIN_PRECISION}) : {best['kind']}"
          + (f", C={best['C']}" if best["kind"] == "logreg" else "")
          + f", seuil={best['threshold']}  →  recall={m['recall']}, precision={m['precision']}")
    print(f"Run MLflow : {best['run_id']}")
    print(f"Modèle sauvegardé dans {settings.model_path}")
    return best["metrics"]


def main(argv: list[str] | None = None) -> dict:
    args = parse_args(argv or [])
    settings = get_settings()
    df = load_data(settings.data_path)
    X_train, X_test, y_train, y_test = split(df)
    if args.grid:
        return grid_search(settings, X_train, X_test, y_train, y_test)

    threshold = args.threshold if args.threshold is not None else settings.threshold
    model, metrics, run_id = train_one(args.model, args.C, threshold,
                                       X_train, X_test, y_train, y_test, settings.data_path)
    save(model, metrics, settings, threshold)
    print(json.dumps(metrics, indent=2))
    print(f"Modèle sauvegardé dans {settings.model_path}")
    print(f"Run MLflow : {run_id}")
    return metrics


if __name__ == "__main__":
    main(sys.argv[1:])
