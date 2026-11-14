# Compte rendu · TP4 : MaintAI devient un package Python

**Groupe :** SUJET 7·  **Membres :*SAFAA HASSANI   ·  **Date :** 12/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP4.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :

```
2 failed, 25 passed, 1 warning in 8.50s
```

Quels sont les deux tests qui échouent, et pourquoi ?

`test_installed_version_matches_the_code` et `test_command_is_declared` échouent car le projet n'est pas encore installé comme distribution Python. Les métadonnées `maintai` ne sont donc pas visibles par `importlib.metadata`, et le point d'entrée `maintai-predict` n'est pas enregistré. Les 25 autres tests passent.

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Vos sections `dependencies` et `[project.scripts]` :

```toml
dependencies = [
   "numpy>=2.0",
   "pandas>=2.2",
   "scikit-learn>=1.7",
   "joblib>=1.4",
]

[project.scripts]
maintai-predict = "maintai.cli:main"
```

Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?

`dependencies` liste uniquement les dépendances nécessaires au cœur du package. `pytest` est un outil de développement, déclaré dans l'extra `dev`; `fastapi` sert à l'API facultative, déclarée dans l'extra `api`. Ils peuvent être installés avec `pip install -e ".[dev,api]"` quand ces fonctions sont nécessaires.

Sortie de `pip show maintai` (les quatre premières lignes) :

```
Name: maintai
Version: 0.2.0
Summary: Prédiction de panne d'équipements industriels à partir de relevés de capteurs.
Home-page:
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
27 passed, 1 warning in 6.21s
```

Placez-vous dans un autre dossier (`cd %TEMP%`) et lancez `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`. Qu'affichent ces deux commandes ? Où Python trouve-t-il le code de `maintai` ?

…
Depuis `%TEMP%`, `maintai-predict 72 6 85 15000` affiche `Probabilité de panne : 95 % (ALERTE)`. `python -c "import maintai; print(maintai.__file__)"` affiche le chemin du fichier `maintai/__init__.py` dans le dossier du projet. `pip install -e .` installe un lien éditable vers les sources du projet, et non une copie indépendante.

Modifiez le message affiché par `maintai/cli.py`, puis relancez `maintai-predict` sans réinstaller. Le changement est-il visible ? Pourquoi ?

Oui. En mode éditable, Python charge directement le code dans l'arborescence du projet; le script généré appelle `maintai.cli:main` depuis ces sources. Le changement de code est donc pris en compte sans réinstallation.

## 3. Sprint 2 : construire et installer le wheel

Sortie de `dir dist` après `python -m build` :

```
Directory: dist

maintai-0.2.0-py3-none-any.whl  11652 octets
maintai-0.2.0.tar.gz            12299 octets
```

Contenu du wheel (`tar -tf dist\maintai-0.2.0-py3-none-any.whl`). Le modèle, les tests et `ui/` y sont-ils ? Pourquoi ?

```
maintai/__init__.py
maintai/cli.py
maintai/client.py
maintai/config.py
maintai/data.py
maintai/dataset.py
maintai/predict.py
maintai/train.py
maintai/api/__init__.py
maintai/api/main.py
maintai/api/schemas.py
maintai/api/security.py
maintai-0.2.0.dist-info/METADATA
maintai-0.2.0.dist-info/WHEEL
maintai-0.2.0.dist-info/entry_points.txt
maintai-0.2.0.dist-info/top_level.txt
maintai-0.2.0.dist-info/RECORD
```

Le wheel contient le code du package et ses métadonnées. Il ne contient ni le modèle, ni les tests, ni `ui/`. Seul `maintai*` est inclus par la configuration setuptools; le modèle est exclu parce qu'il est un artefact de déploiement externe.

Dans un environnement neuf (`%TEMP%\maintai-tp4-wheel-test`), installez le wheel et lancez `maintai-predict` :

| Étape | Ce qui s'affiche |
|---|---|
| sans `MAINTAI_MODELS_DIR` | `Modèle introuvable` sous `Lib/site-packages/models/model.joblib`; le programme indique de définir `MAINTAI_MODELS_DIR`. |
| avec `MAINTAI_MODELS_DIR` vers vos `models` | Avertissements `InconsistentVersionWarning` avec scikit-learn 1.9.1, puis `Probabilité de panne : 95 % (ALERTE)`. |
| après `pip install scikit-learn==1.8.0` | `Probabilité de panne : 95 % (ALERTE)`, sans avertissement de version. |

D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?

Le modèle sérialisé par joblib a été entraîné avec scikit-learn 1.8.0, mais le wheel installé dans l'environnement neuf accepte toute version `>=1.7` et pip y a installé scikit-learn 1.9.1. Le chargement signale cette différence de version, qui peut compromettre la compatibilité. Dans `models/model_info.json`, la ligne est `"sklearn_version": "1.8.0"`. Installer cette version précise supprime l'avertissement.

## 4. Questions de compréhension

1. Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?
   `requirements.txt` fige les versions d'un environnement complet de travail (application, API, interface et tests) pour reproduire le TP. `dependencies` déclare les dépendances minimales du package distribué, ici le cœur prédiction, avec des bornes de versions plutôt que des versions exactes.
2. Quelle différence entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?
   `pip install -e .` installe le projet en mode éditable et pointe vers les sources de travail; les modifications du code sont visibles immédiatement. L'installation du wheel copie une distribution construite dans l'environnement; les modifications des sources ne sont pas visibles sans reconstruire et réinstaller le wheel.
3. Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict.exe` ?
   C'est une association entre une commande shell et une fonction Python, ici `maintai-predict` vers `maintai.cli:main`. Sous Windows, pip crée `maintai-predict.exe` dans le dossier `Scripts` de l'environnement Python où le package est installé, par exemple `.venv\Scripts\maintai-predict.exe`.

## 5. Le rendu Git

- Lien de la pull request : non disponible dans ce dossier local.
- Le tag `tp4` existe sur GitHub : impossible à vérifier ici; ce dossier ne contient pas de dépôt Git (`git rev-parse --show-toplevel` échoue).
- `git status` avant le commit : impossible à vérifier sans dépôt Git. Après la construction, `dist/` et `maintai.egg-info/` existent; ils sont ignorés par `.gitignore` (tout comme `build/`).

## 6. Ce qui reste flou

Aucun point bloquant restant identifié pendant les tests locaux. La création de la pull request et du tag reste à faire dans le dépôt Git distant du cours.
