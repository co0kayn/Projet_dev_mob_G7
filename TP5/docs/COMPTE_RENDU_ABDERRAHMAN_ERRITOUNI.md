# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** G1  ·  **Membres :** Abderrahman Erritouni  ·  **Date :** 19/11/2026, 12:07

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
FAILED tests/test_tracking.py::test_training_creates_a_run - AssertionError: aucun run MLflow : log_run n'a rien enregistré
FAILED tests/test_tracking.py::test_run_records_metrics - AssertionError: ...
FAILED tests/test_tracking.py::test_run_records_data_version - AssertionError: ...
FAILED tests/test_tracking.py::test_run_stores_the_model - AssertionError: ...
FAILED tests/test_tracking.py::test_options_change_the_run - AssertionError: ...
5 failed, 27 passed in 7.56s
```

Quels tests échouent, et pourquoi ?

Les 5 tests de `tests/test_tracking.py`. Dans le starter, `log_run` ne contient qu'un TODO et renvoie `""` : aucun run n'est enregistré dans MLflow, donc `mlflow.search_runs(...)` ne trouve rien (« aucun run MLflow : log_run n'a rien enregistré »). Les 27 autres tests (données, entraînement, API, client, CLI, UI, package) viennent du TP4 et passent toujours.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

Avant : vers le dossier `TP/TP4` (installation éditable faite au TP4). Après : vers `TP/TP5` (`pip show maintai` → *Editable project location: …\TP5*, version 0.3.0). C'est pour cela que `test_installed_version_matches_the_code` échoue si on oublie `pip install -e .`.

## 2. Sprint 1 : MLflow

Votre fonction `log_run` (`maintai/tracking.py`) :

```python
def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """Enregistre un entraînement : paramètres, version des données, métriques et modèle. Renvoie l'id du run."""
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_param("data_md5", file_md5(data_path))
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_example,
            skops_trusted_types=TRUSTED_TYPES,
        )
        return run.info.run_id
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
32 passed, 4 warnings in 20.43s
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») — données v1, n_train = 4000 :

| Commande | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train` | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --C 0.01` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train --model forest --threshold 0.2` | 0.831 | 0.479 | 0.854 |

(Baseline « toujours pas de panne » : accuracy 0.864, recall 0.0.)

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

La régression logistique avec `--threshold 0.2` (run `34315775ad1b42f9a474bb8be636c27d`) : c'est le meilleur recall (0.838), donc le moins de pannes manquées. On accepte en échange une precision plus faible (0.543), c'est-à-dire plus de fausses alertes, ce qui coûte moins cher qu'une panne. La forêt aléatoire n'est pas meilleure : à seuil égal, elle a un recall **et** une precision plus faibles que la régression logistique (0.728/0.562 contre 0.750/0.622 au seuil 0.3 ; 0.831/0.479 contre 0.838/0.543 au seuil 0.2), pour un modèle bien plus lourd (≈ 8,5 Mo) et moins explicable. `C = 0.01` (plus de régularisation) fait baisser le recall : mauvais sens pour nous. On note aussi que l'accuracy est trompeuse : la baseline atteint 0.864 sans jamais détecter une panne.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

`scikit-learn==1.8.0` (avec `mlflow==3.18.0`, `numpy==2.4.4`, `pandas==3.0.2`, `skops==0.16.0`…). Au TP4, le fichier `model.joblib` ne disait pas avec quelle version de scikit-learn il avait été entraîné (il fallait l'écrire à la main dans `model_info.json`) : le recharger avec une autre version pouvait échouer ou donner des résultats différents. Ici, chaque modèle est livré avec la liste exacte de ses dépendances, on peut recréer l'environnement qui l'a produit.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

Dans le dossier courant `TP/TP5` : `mlflow.db` (base SQLite : paramètres, métriques, tags de chaque run) et `mlruns/1/models/m-…/artifacts/` (le modèle `model.skops`, `MLmodel`, `requirements.txt`, `conda.yaml`, l'exemple d'entrée). Ils ne vont pas dans Git (exclus par le `.gitignore`) : ce sont des fichiers générés, binaires, qui grossissent à chaque entraînement et qui sont propres à chaque machine ; les mettre dans Git provoquerait des conflits sur la base SQLite et alourdirait le dépôt. Git garde le code qui permet de les reproduire.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: 126815
  hash: md5
  path: sensors.csv
```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

C'est exactement la même valeur : `73e0b7cb3c6f795c70c3ddf970b99c15`. `file_md5()` de `tracking.py` calcule le même md5 que DVC. Le `data_md5` d'un run MLflow désigne donc une version précise du fichier de données, retrouvable via le reçu `.dvc` dans Git : c'est ce qui relie un modèle à ses données.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

`sensors.csv` est un fichier de données qui peut devenir gros (127 Ko ici, 100 Mo ou plus en vrai) : Git gère mal les gros fichiers et en garde chaque version pour toujours, ce qui alourdit le dépôt. DVC le garde hors de Git (dans `.dvc/cache` puis dans le stockage) et ne met dans Git qu'un **reçu** de 4 lignes (`sensors.csv.dvc` : md5 + taille, ~100 octets). Git versionne le reçu ; le reçu dit à DVC quel fichier ramener.

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
data\sensors.csv.dvc:
	changed outs:
		modified:           data\sensors.csv
```

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | `e59650c` Données v1 (5000 relevés) | `73e0b7cb` | 5000 |
| v2 | `ac70942` Données v2 (8000 relevés) | `93fdeef2` | 8000 |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

Après `git checkout e59650c -- data/sensors.csv.dvc` puis `dvc checkout` : **5000 lignes**. `git status` montre alors `M data/sensors.csv.dvc` (l'ancien reçu) : on ne le commite pas. Retour à la v2 avec `git checkout HEAD -- data/sensors.csv.dvc` puis `dvc checkout` : **8000 lignes**. Git choisit le reçu, DVC ramène le fichier correspondant depuis son cache.

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

```
A       data\sensors.csv
1 file fetched and 1 file added
```

DVC lit le reçu `data/sensors.csv.dvc`, télécharge le fichier qui a ce md5 depuis le stockage (`%USERPROFILE%\dvc-stockage`) vers le cache (`dvc fetch`), puis le recopie dans `data/` (`dvc checkout`). Le fichier revient avec ses 8000 lignes (v2). C'est la situation d'un coéquipier qui clone le dépôt sans avoir les données.

## 4. Relier modèle et données

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages (logreg, C = 1.0, seuil 0.3) :

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 (`6d2d7a40…`) | `73e0b7cb` | 4000 | 0.750 | 0.622 |
| v2 (`bcebb433…`) | `93fdeef2` | 6400 | 0.741 | 0.650 |

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

Non. Le recall v2 est légèrement plus bas (0.741 contre 0.750) et la precision un peu plus haute (0.650 contre 0.622) : les écarts sont petits et ne vont pas dans le même sens. Surtout, les deux runs ne sont pas évalués sur le **même jeu de test** : chaque run découpe ses propres données (1000 relevés de test en v1, 1600 en v2, autre graine de génération, taux de panne différent). Les métriques mesurent donc à la fois le modèle et la difficulté de son jeu de test. Pour conclure, il faudrait évaluer les deux modèles sur un même jeu de test fixe (et idéalement plusieurs découpages). Ce qu'on peut dire : grâce au `data_md5` et au `n_train`, on sait exactement sur quelles données chaque chiffre a été obtenu.

## 5. Décision : l'ADR 004

Voir `docs/adr/004-choix-du-modele.md` : régression logistique, C = 1.0, **seuil 0.2**. Run MLflow `34315775ad1b42f9a474bb8be636c27d`, données `data_md5 = 73e0b7cb3c6f795c70c3ddf970b99c15` (v1, commit `e59650c`). Recall 0.838, precision 0.543 : on accepte plus de fausses alertes pour manquer moins de pannes.

## 6. Questions de compréhension

1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?
   **Git** versionne le code (et les petits fichiers texte : config, ADR, reçus `.dvc`). **DVC** versionne les fichiers de données : il les garde dans un cache et un stockage, et ne met dans Git qu'un reçu (md5 + taille). **MLflow** garde la trace de chaque entraînement (run) : paramètres, `data_md5`, métriques, modèle et versions exactes des bibliothèques, pour comparer les runs entre eux.
2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?
   Le stockage est un dossier de **mon** PC (`%USERPROFILE%\dvc-stockage`) : son chemin n'a pas de sens sur la machine d'un coéquipier, donc il est écrit dans `.dvc/config.local`, ignoré par Git, au lieu de `.dvc/config`. Pour partager, il faudrait un stockage accessible à tous (S3, Google Drive, Azure, serveur SSH/dossier réseau), déclaré **sans** `--local` dans `.dvc/config` et commité ; chacun ferait alors `dvc pull` après `git pull`.
3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?
   Le **code** : Git (et le wheel du TP4). Les **données** : DVC, le reçu `.dvc` dans Git et le fichier dans le stockage. Le **modèle** (avec ses versions exactes) : MLflow, un run identifié par son `run_id`, avec le `requirements.txt` du modèle.

## 7. Le rendu Git

- Lien de la pull request : pas encore créée. Le travail est commité dans le dépôt local (commits `DVC : init`, `Données v1`, `Données v2`, `TP5 : compte rendu et ADR 004`) ; il reste à le pousser sur le dépôt GitHub du groupe (branche `tp5`) et à ouvrir la pull request.
- Le tag `tp5` existe sur GitHub : non (créé en local, à pousser avec `git push --tags`)
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? non (exclus par `.gitignore`, `data/.gitignore` et `.dvc/.gitignore` ; `.dvc/config.local` non plus)

## 8. Ce qui reste flou

Comment comparer proprement deux modèles entraînés sur des versions de données différentes (garder un jeu de test fixe versionné à part ?), et comment MLflow et DVC s'utilisent quand le stockage est partagé par toute l'équipe (droits d'accès, coût du stockage).
