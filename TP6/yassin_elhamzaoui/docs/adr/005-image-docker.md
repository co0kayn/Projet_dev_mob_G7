# ADR 005 : modèle Dockerisé ou monté en volume

Date : 26/11/2026 · Auteurs : à renseigner

## Contexte

MaintAI doit pouvoir démarrer sur une machine Docker sans préparer un environnement Python local. Le code et les dépendances changent moins souvent que les données et le modèle entraîné; les secrets ne doivent pas être distribués avec l'image.

## Options étudiées

1. **Inclure le modèle dans l'image** : l'image est autonome et chaque version publiée contient exactement le code et le modèle correspondants. En contrepartie, chaque nouvel entraînement nécessite une reconstruction et une redistribution de l'image, qui devient plus volumineuse.
2. **Monter le modèle depuis l'hôte** : le modèle peut être remplacé sans reconstruire l'image et reste hors de l'image. En contrepartie, le déploiement doit fournir le bon dossier et s'assurer que le modèle correspond au code.

## Décision

L'image `maintai:0.4.0` contient le code et les dépendances figées; `models/` et `data/` sont montés au lancement en lecture seule. Le fichier `.dockerignore` exclut `models/`, `data/`, `.env`, `mlflow.db`, `mlruns/` et `.dvc/`; la clé API est fournie au service API via `env_file: .env` et n'entre jamais dans l'image.

## Conséquences

Un modèle ou un jeu de données peut être remplacé sans reconstruire l'image, et les conteneurs ne peuvent pas modifier les fichiers montés. Le déploiement doit fournir les dossiers et fichiers attendus, garder le modèle compatible avec le code et protéger le fichier `.env`; le statut de santé signale si le modèle est absent.
