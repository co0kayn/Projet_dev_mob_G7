# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)
**Groupe :** G7 · **Membres :** YASSIN ELHAMZAOUI · **Date :** 19/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP5.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
(à recoller : la sortie obtenue AVANT d'écrire log_run)
```

Quels tests échouent, et pourquoi ?

Ce sont les tests de `tests/test_tracking.py` (`test_training_creates_a_run`, `test_run_records_metrics`, `test_run_records_data_version`, `test_run_stores_the_model`, `test_options_change_the_run`). Ils échouent parce que la fonction `log_run` de `maintai/tracking.py` n'est pas encore écrite : aucun run n'arrive dans MLflow, donc `mlflow.search_runs` ne trouve rien (« aucun run MLflow : log_run n'a rien enregistré »). Comme `train.main()` appelle `log_run`, les tests d'entraînement peuvent échouer eux aussi. Les autres tests (API, sécurité, CLI, client, données, package, UI) passent.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

Avant : `maintai` pointait vers le dossier du TP précédent (`TP/TP4`), celui où on avait lancé `pip install -e .` au TP4. Python importait donc l'ancien code (version 0.2.0), sans `tracking.py`. Après : `pip show maintai` donne `Editable project location: C:\Users\...\session7\TP5`. Le package pointe sur le code du TP5 (version 0.3.0).

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
32 passed, 4 warnings in 17.43s
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») :

| Commande | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train` | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --C 0.01` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train --model forest --threshold 0.2` | 0.831 | 0.479 | 0.854 |

(Baseline « jamais de panne » : accuracy 0.864, recall 0.0. Tous les runs ont `n_train = 4000` et `data_md5 = 73e0b7cb…`.)

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

Je choisirais **la régression logistique avec C = 1.0 et un seuil de 0.2** (run `bdafb172049c4f9e87f6561dd1e0f72d`). C'est le meilleur recall : on détecte 83,8 % des pannes, contre 75 % au seuil 0.3. On perd un peu de precision (0.543) et d'accuracy (0.882), ce qui veut dire plus de fausses alertes. C'est acceptable, car une fausse alerte coûte moins cher qu'une panne manquée. La random forest au même seuil fait moins bien sur le recall et sur la precision, donc elle n'apporte rien. On ne choisit pas non plus le run qui a la meilleure accuracy (C = 0.01) : c'est lui qui manque le plus de pannes. L'accuracy trompe ici, puisque la baseline atteint déjà 86,4 %.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

Le `requirements.txt` du modèle indique `scikit-learn==1.8.0`, avec `numpy==2.4.4`, `pandas==3.0.2`, `scipy==1.17.1` et `skops==0.16.0`. Au TP4, un modèle `joblib` chargé avec une autre version de scikit-learn que celle de l'entraînement donnait un avertissement (`InconsistentVersionWarning`) ou des résultats faux, et on devait noter la version à la main dans `model_info.json`. Avec MLflow, chaque modèle part avec ses dépendances exactes (`requirements.txt`, `conda.yaml`, `python_env.yaml`). On peut donc recréer le bon environnement pour le charger.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

Les paramètres, les métriques et les métadonnées des runs sont dans la base SQLite `mlflow.db`, à la racine de `TP5`. Les artefacts (modèle `model.skops`, `MLmodel`, `requirements.txt`, exemples d'entrée) sont dans `mlruns/1/models/m-<id>/artifacts/`. Aucun de ces fichiers ne va dans Git (ils sont dans le `.gitignore`), pour trois raisons : ce sont des fichiers binaires et lourds qui grossissent à chaque entraînement, ils sont propres à chaque machine, et Git versionne du code, pas des résultats d'expériences. Pour partager les runs, il faudrait un serveur MLflow commun.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
(à coller : sortie de cat data/sensors.csv.dvc)
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: …
  hash: md5
  path: sensors.csv
```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

Les deux valeurs sont identiques (`73e0b7cb3c6f795c70c3ddf970b99c15`). `file_md5` dans `tracking.py` calcule la même empreinte MD5 que DVC. Le run MLflow et le fichier `.dvc` désignent donc la même version des données, et on peut savoir sur quelles données exactes un modèle a été entraîné.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

Le CSV contient les données : il est lourd, il change à chaque nouvelle version, et Git gère mal les gros fichiers (le dépôt garderait toutes les copies pour toujours). C'est DVC qui le stocke, dans son cache puis dans le stockage distant. Le fichier `.dvc` ne fait que quelques lignes (md5, taille, chemin) : c'est un pointeur vers une version précise des données. Le mettre dans Git suffit à associer chaque commit à une version des données.

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
(à coller)
data\sensors.csv.dvc:
        changed outs:
                modified:           data\sensors.csv
```

DVC voit que le fichier ne correspond plus à l'empreinte enregistrée dans le `.dvc`. Il faut relancer `dvc add`, puis commiter le `.dvc`.

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | … | 73e0b7cb | 5 001 (5 000 relevés + en-tête) |
| v2 | … | … | 8 001 (8 000 relevés + en-tête) |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

On retrouve 5 001 lignes (5 000 relevés et l'en-tête). `dvc checkout` remet dans `data/` le fichier du cache qui correspond au md5 du `.dvc` de la v1. Après être revenu à la v2 (`git checkout HEAD -- data/sensors.csv.dvc`, puis `dvc checkout`), on retrouve 8 001 lignes.

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

`dvc pull` va chercher dans le stockage distant (`C:/dvc-stockage`) le fichier qui correspond au md5 du `.dvc`. Il le recopie dans le cache, puis le replace dans `data/sensors.csv`. Les données reviennent à l'identique (même md5). Cela montre que les données sont sauvegardées ailleurs que sur le poste de travail et qu'on peut les récupérer à partir du seul dépôt Git.

## 4. Relier modèle et données

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages :

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 | 73e0b7cb | 4000 | 0.750 | 0.622 |
| v2 | … | 6400 | … | … |

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

Pas directement. Les deux modèles ne sont pas évalués sur le même jeu de test : il est tiré de données différentes (1 000 lignes en v1, 1 600 en v2, avec une autre graine et peut-être une autre proportion de pannes). Un meilleur recall peut venir d'un jeu de test plus facile, et pas d'un meilleur modèle. Pour comparer de façon juste, il faut évaluer les deux modèles sur le même jeu de test, fixe et à part. On ne peut comparer que des runs qui ont le même `data_md5` et le même jeu de test. Le `data_md5` enregistré dans MLflow sert justement à repérer ces cas.

## 5. Décision : l'ADR 004

Voir `docs/adr/000-modele.md`, à recopier dans `docs/adr/004-choix-du-modele.md`. Modèle retenu : **régression logistique, C = 1.0, seuil 0.2**. Run MLflow `bdafb172049c4f9e87f6561dd1e0f72d` (recall 0.838, precision 0.543, accuracy 0.882), données `data_md5 = 73e0b7cb3c6f795c70c3ddf970b99c15` (v1, 5 000 lignes).

## 6. Questions de compréhension

1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?
   **Git** versionne le code et les petits fichiers texte : le code source, la configuration, les ADR, les fichiers `.dvc`. **DVC** versionne les données (et les gros fichiers) : il les stocke dans un cache et un stockage distant, et Git ne garde que leur empreinte md5. **MLflow** garde la trace des expériences : pour chaque entraînement, il enregistre les paramètres, les métriques, le modèle produit avec ses dépendances, et la version des données (`data_md5`). Ensemble, ils répondent à trois questions : quel code (Git), quelles données (DVC), quel modèle et quels résultats (MLflow).
2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?
   Avec `--local`, la configuration du stockage est écrite dans `.dvc/config.local`, qui n'est pas commité. Le chemin `C:/dvc-stockage` n'existe que sur notre machine, et chacun peut avoir un chemin différent sans casser la configuration des autres. Pour partager les données avec tout le groupe, il faudrait un stockage distant commun et accessible à tous (S3, Google Drive, Azure Blob, serveur SSH, dossier réseau partagé), déclaré sans `--local` dans `.dvc/config` et commité. Chacun aurait aussi besoin des identifiants d'accès, qu'il faut garder hors de Git.
3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?
   (1) **Le code** (prétraitement, prédiction, API) : dans Git, et installable comme package avec `pyproject.toml`. (2) **Le modèle entraîné** (les poids) : dans les artefacts MLflow (`mlruns/.../model.skops`, que l'on charge avec `runs:/<id>/model`), et aussi dans `models/model.joblib` pour l'API. (3) **L'environnement**, c'est-à-dire les versions exactes des bibliothèques : dans `requirements.txt` à la racine du projet, et dans le `requirements.txt`, le `conda.yaml` et le `python_env.yaml` enregistrés par MLflow avec chaque modèle. Les données qui ont servi à l'entraînement sont maintenant suivies par DVC, et reliées au modèle par le `data_md5` du run.

## 7. Le rendu Git

- Lien de la pull request : …
- Le tag `tp5` existe sur GitHub : oui / non
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? Non. `mlflow.db`, `mlruns/` et `data/*.csv` sont dans le `.gitignore`, et `.dvc/cache` est ignoré par le `.gitignore` interne de `.dvc/`.

## 8. Ce qui reste flou

…
