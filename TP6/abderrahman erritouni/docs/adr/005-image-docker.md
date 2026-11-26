# ADR 005 : le modèle arrive par un volume, l'image ne porte que le code

Date : 26/11/2026 · Auteurs : Abderrahman Erritouni

## Contexte
MaintAI doit tourner sur un serveur où personne ne prépare de `.venv` : on l'emballe dans une image Docker
(`maintai:0.4.0`). Il faut décider ce qui entre dans l'image et ce qui arrive au lancement, en particulier
le modèle (`models/model.joblib`), qui est réentraîné plus souvent que le code ne change (TP5, MLOps).

## Options étudiées
1. **Modèle dans l'image** (`COPY models ./models`) :
   - gagne : une image autonome, un seul artefact à livrer, code et modèle toujours cohérents ;
   - perd : chaque réentraînement impose un nouveau build et une nouvelle version d'image ; l'image grossit ;
     un modèle (et ses données d'entraînement implicites) part avec toute image partagée.
2. **Modèle par un volume** (`-v ./models:/app/models:ro`, `volumes:` dans `compose.yaml`) :
   - gagne : on change de modèle sans reconstruire ni redéployer le code ; image plus légère et réutilisable ;
     lecture seule (`:ro`), le conteneur ne peut pas abîmer le modèle ;
   - perd : l'image seule ne suffit pas, il faut fournir le dossier `models/` au lancement ; si on l'oublie,
     l'API démarre mais `/health` dit `model_loaded: false` et `/v1/predict` répond 503 (vérifié, piège 1).

## Décision
Option 2 : le modèle et les données arrivent par des volumes en lecture seule, la clé par `--env-file .env` /
`env_file:`. Raison principale : le modèle change sans nouveau code (séance 7) ; le lier à l'image obligerait
à reconstruire pour chaque réentraînement. C'est la même règle que le wheel du TP4 : le paquet porte le code,
pas le modèle.

`.dockerignore` laisse dehors :
- `data/`, `models/` : arrivent par volume (raison ci-dessus) ;
- `.env` : un secret n'entre jamais dans une image qu'on peut partager ;
- `mlflow.db`, `mlruns/`, `.dvc/` : suivi et versionnement de l'entraînement, inutiles pour servir le modèle ;
- `.venv/`, `tests/`, `.git/`, caches, `build/`, `dist/` : lourds ou locaux, l'image installe ses propres
  bibliothèques depuis `requirements-docker.txt`.
L'autre option (tout copier) ferait gagner un `COPY .` plus simple, mais perdre en taille, en temps de build
(contexte envoyé à chaque build) et en sécurité (clé dans l'image).

## Conséquences
- Facilite : réentraîner puis redémarrer le conteneur suffit ; une seule image pour tous les modèles.
- Rend plus difficile : déployer exige de livrer aussi `models/` (et `.env`) à côté de l'image.
- À surveiller : la compatibilité entre le modèle monté et les bibliothèques de l'image (scikit-learn figé
  à 1.8.0 dans `requirements-docker.txt`) ; `/health` doit être vérifié après chaque lancement.
