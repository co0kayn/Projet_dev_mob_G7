# Rapport de travail

**Nom :** Yassin Elhamzaoui
**Date :** 22 octobre 2026
**Projet :** Projet de prédiction des repas servis

## Travail réalisé

- Préparation du projet Python avec sa structure de données, de code, de tests et de documentation.
- Ajout du projet dans le dépôt GitHub `Projet_dev_mob_G7`, dans le dossier `TP0`.
- Configuration du modèle pour prédire la colonne `repas_servis` du fichier `data/cantine_repas.csv`.
- Configuration du problème en régression avec la métrique principale `mae`.
- Configuration d'un découpage chronologique des données, avec la colonne `date` et les jours les plus récents réservés au test.
- Vérification du fonctionnement de la configuration et clarification du fait que `config.py` ne produit pas d'affichage lorsqu'il est exécuté seul.
- Installation des dépendances Python dans l'environnement virtuel `.venv`.
- Exécution de la suite de tests : **8 tests réussis**.
- Exécution de l'entraînement et comparaison des modèles.

## Résultats obtenus

| Modèle | MAE | RMSE | R2 |
|---|---:|---:|---:|
| Régression linéaire | 22.239 | 28.170 | 0.883 |
| Random forest | 31.845 | 41.540 | 0.746 |
| Arbre de décision | 46.000 | 59.710 | 0.475 |
| Baseline (moyenne) | 70.271 | 88.416 | -0.151 |

La régression linéaire est le meilleur modèle selon la MAE.

## Commandes utilisées

```bash
source .venv/bin/activate
python -m pytest
python -m monprojet.train
python -c "from monprojet import config; print(config.TARGET, config.TASK, config.MAIN_METRIC)"
```

## Remarque

Une configuration alternative pour un problème de classification sur `data/maintai.csv` a été étudiée, mais ce fichier n'était pas présent dans le projet. La configuration actuellement conservée concerne donc la régression des repas servis.
