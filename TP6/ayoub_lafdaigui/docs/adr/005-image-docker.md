# ADR 005 : le modèle arrive par un volume, l'image ne porte que le code

Date : 26/11/2026 · Auteurs : Ayoub Lafdaigui

## Contexte

MaintAI doit tourner sur une machine où personne ne prépare de `.venv` : on l'emballe dans une image Docker (`maintai:0.4.0`). Il faut décider ce qui entre dans l'image et ce qui arrive au lancement, en particulier le modèle (`models/model.joblib`), qui est réentraîné plus souvent que le code ne change (TP5).

## Options étudiées

1. **Modèle dans l'image** (`COPY models ./models`) :
   - gagne : une image autonome, un seul artefact à livrer, code et modèle toujours cohérents ;
   - perd : chaque réentraînement impose un nouveau build et une nouvelle version d'image ; l'image grossit ; le modèle part avec toute image partagée.
2. **Modèle par un volume** (`-v ./models:/app/models:ro`, `volumes:` dans `compose.yaml`) :
   - gagne : on change de modèle sans reconstruire l'image ; la même image sert tous les modèles ; la lecture seule (`:ro`) empêche le conteneur d'abîmer le modèle ;
   - perd : l'image seule ne suffit pas, il faut fournir le dossier `models/` au lancement ; si on l'oublie, l'API démarre mais `/health` annonce `model_loaded: false` et `/v1/predict` répond 503.

## Décision

Option 2. L'image contient le code (`maintai/`, `ui/`) et les bibliothèques figées (`requirements-docker.txt`). Le modèle (`models/`) et les données (`data/`) sont montés au lancement en lecture seule ; la clé API arrive par `env_file: .env`. C'est la même règle que pour le wheel du TP4 : le paquet porte le code, pas le modèle.

Le fichier `.dockerignore` laisse dehors :

- `data/`, `models/` : ils arrivent par volume ;
- `.env` : un secret n'entre jamais dans une image qu'on peut partager ;
- `mlflow.db`, `mlruns/`, `.dvc/` : suivi et versionnement de l'entraînement, inutiles pour servir le modèle ;
- `.venv/`, `tests/`, `.git/`, caches, `build/`, `dist/` : lourds ou locaux.

## Conséquences

- Facilite : réentraîner puis redémarrer le conteneur suffit ; une seule image pour tous les modèles ; aucun secret ni modèle dans l'image.
- Rend plus difficile : un déploiement doit livrer `models/` (et `.env`) à côté de l'image.
- À surveiller : la compatibilité entre le modèle monté et les bibliothèques de l'image (scikit-learn figé à 1.8.0) ; vérifier `/health` après chaque lancement.
