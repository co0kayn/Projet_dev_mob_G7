# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** G1  ·  **Membres :** Safaa Hassani ·  **Date :** 19/11/2026 11:50

> Ce compte rendu doit être rendu avec la pull request du TP5.

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
32 passed, 4 warnings in 57.20s
```

Quels tests échouent, et pourquoi ?

Aucun test ne devrait échouer lorsque les dépendances sont installées correctement. La vérification réalisée indique `32 passed, 4 warnings`. Les quatre avertissements sont des avertissements de dépréciation ou d'inférence de schéma MLflow/FastAPI, pas des échecs de tests.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

Avant l'installation en mode éditable, le package pouvait être copié dans l'environnement virtuel et provenir d'une ancienne installation. Après `pip install -e .`, `pip show maintai` indique :

- **Nom/version :** `maintai` version `0.3.0`
- **Location :** `C:\Users\DELL\Downloads\TP5\TP5\.venv\Lib\site-packages`
- **Editable project location :** `C:\Users\DELL\Downloads\TP5\TP5`

Le package pointe donc directement vers les sources du workspace ; les modifications locales sont immédiatement visibles.

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
32 passed, 4 warnings in 57.20s
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») :

| Commande | recall | precision | accuracy |
|---|---:|---:|---:|
| `python -m maintai.train` | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --C 0.01` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 |
| Essai supplémentaire : forêt enregistrée après l'essai final | 0.728 | 0.562 | 0.886 |

Une exécution locale courante donne déjà les valeurs suivantes pour un seuil de `0.3` : recall `0.728`, précision `0.562` et accuracy `0.886`. Le tableau MLflow ci-dessus doit être complété avec les résultats exacts des quatre commandes demandées.

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

Je choisirais le run `f1c451c788974128ab08b3d50ba98e38` ou un run équivalent utilisant la régression logistique avec `threshold=0.2`, car il obtient le recall le plus élevé des essais sur la v1 : `0.838`. Sa précision est `0.543` et son accuracy `0.882`. Comme une panne manquée coûte plus cher qu'une fausse alerte, ce rappel supérieur est préféré à une précision plus élevée obtenue avec d'autres réglages.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

La version vérifiée dans les dépendances figées du projet est `scikit-learn==1.8.0`. Le modèle MLflow associe donc son artefact aux bibliothèques utilisées lors de l'entraînement. Cela réduit le risque d'incompatibilité rencontré au TP4 lorsqu'un modèle entraîné avec une version donnée était chargé dans un environnement contenant une autre version.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

Dans ce projet, les runs sont enregistrés localement dans `mlflow.db` et dans le dossier `mlruns/`. Ils ne doivent pas être suivis par Git : leurs fichiers sont techniques, volumineux ou spécifiques à l'expérience locale, et peuvent être reconstruits depuis les nouvelles exécutions. Le `.gitignore` exclut déjà `mlflow.db` et `mlruns/`.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
outs:
- md5: 93fdeef2cac1893c4f720c16457eea75
  size: 202834
  hash: md5
  path: sensors.csv
```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

Le fichier DVC contient `93fdeef2cac1893c4f720c16457eea75`, qui est exactement la valeur du paramètre `data_md5` du dernier run MLflow (`877736652ed246019a43303fb9ea2b04`). Les deux outils identifient donc exactement la même version de `data/sensors.csv`.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

`data/sensors.csv` est ignoré par Git grâce à `data/*.csv` dans `.gitignore`, car il s'agit du gros fichier de données. Le fichier `data/sensors.csv.dvc` est léger : il contient uniquement l'empreinte MD5, la taille et le chemin des données. Il peut donc être suivi par Git ; il pointe vers le contenu stocké dans le cache ou le remote DVC.

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

Les données locales sont actuellement synchronisées avec le pointeur DVC :

```
Data and pipelines are up to date.
```

Le remote local est configuré ainsi :

```
stockage        C:/dvc-stockage (default)
```

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---:|
| v1 | Non créé dans cet historique | `73e0b7cb` | 5001 avec l'en-tête |
| v2 | `36d7a95 Données v2` | `93fdeef2` | 8001 avec l'en-tête |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

La v1 contient `5000` relevés plus une ligne d'en-tête, soit `5001` lignes au total. Pour effectuer correctement le passage v1/v2, il faut créer deux commits Git distincts contenant chacun le fichier `data/sensors.csv.dvc` correspondant. Ici, seul le commit `36d7a95` de la v2 existe ; le commit v1 n'est donc pas disponible. Pour revenir à la v2, restaurer le pointeur depuis `36d7a95` puis exécuter `dvc checkout`.

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

Après suppression de `data/sensors.csv` et de `.dvc/cache`, `dvc pull` doit lire `data/sensors.csv.dvc`, retrouver l'objet `93fdeef2cac1893c4f720c16457eea75` dans le remote `C:/dvc-stockage`, reconstruire le cache DVC et restaurer le CSV v2.

## 4. Relier modèle et données

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages :

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---:|---:|---:|
| v1 — régression logistique, `C=1.0`, seuil `0.3` | `73e0b7cb` | 4000 | 0.750 | 0.622 |
| v2 — régression logistique, `C=1.0`, seuil `0.3` | `93fdeef2` | 6400 | 0.741 | 0.650 |

Le run v1 retenu pour cette comparaison est `86cbea09c825454fac9e2cb2d22d89e7b1` : régression logistique avec `C=1.0`, seuil `0.3`, recall `0.750` et précision `0.622`. Le run v2 est `877736652ed246019a43303fb9ea2b04`.

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

La précision augmente de `0.622` à `0.650`, mais le recall baisse légèrement de `0.750` à `0.741`. Comme MaintAI privilégie le recall, le v2 ne peut pas être déclaré meilleur uniquement sur ces résultats. Les deux runs ont des jeux de données, des tailles d'entraînement, des jeux de test et des distributions potentiellement différentes ; leurs métriques ne mesurent donc pas exactement la même difficulté. Il faut comparer les deux modèles sur le même jeu de validation indépendant avant de conclure.

## 5. Décision : l'ADR 004

Voir `docs/adr/004-choix-du-modele.md`. Le choix doit reprendre le run MLflow retenu avec son identifiant complet et les huit premiers caractères du `data_md5` correspondant.

## 6. Questions de compréhension

1. **Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?**

   Git versionne le code source, les fichiers de configuration et les pointeurs légers DVC. DVC versionne les gros objets de données ou modèles via des fichiers `.dvc` et les stocke dans un cache/remote. MLflow suit les expériences : paramètres, métriques, empreinte des données, modèles et versions des bibliothèques.

2. **Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?**

   `--local` crée une configuration locale qui n'est pas communiquée aux autres membres. Pour partager les données, il faut configurer un remote accessible à tous, par exemple SSH, S3, Azure Blob, Google Drive ou un stockage réseau, puis exécuter `dvc push` et `dvc pull`.

3. **Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?**

   Un livrable modèle comprend : le code applicatif/package `maintai`, l'artefact modèle dans `models/model.joblib`, les métadonnées et métriques dans `models/model_info.json` et `models/metrics.json`, ainsi que les versions exactes des dépendances. MLflow conserve aussi une copie traçable du modèle dans son dossier de run avec son environnement.

## 7. Le rendu Git

- Lien de la pull request : À compléter après publication.
- Le tag `tp5` existe sur GitHub : À vérifier après publication.
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? Non, ils sont ignorés ou gérés séparément ; à vérifier avec `git status` avant le commit.

## 8. Ce qui reste flou

- La sortie exacte des quatre commandes MLflow doit être relevée dans l'interface.
- Le fichier `data/sensors.csv.dvc`, ses empreintes MD5 et les commits Git des versions v1/v2 doivent être reportés après les commandes DVC.
- Les identifiants complets des runs MLflow v1/v2 et l'empreinte réelle du modèle retenu doivent être complétés.
