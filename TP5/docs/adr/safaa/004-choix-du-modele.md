# ADR 004 : choix du modèle pour MaintAI

Date : 19/11/2026 · Auteur : Safaa Hassani

## Contexte

MaintAI doit détecter les pannes à partir des relevés de capteurs. Une panne manquée entraîne un coût plus élevé qu'une fausse alerte : le rappel (recall) est donc prioritaire, tout en conservant une précision suffisamment élevée pour éviter de générer trop d'alertes inutiles.

Plusieurs modèles et seuils ont été évalués avec MLflow sur les mêmes données synthétiques. Les expériences permettent de comparer les réglages à partir du recall, de la précision, de l'accuracy, des paramètres du modèle et de l'empreinte `data_md5`.

## Options étudiées

1. **Régression logistique avec seuil `0.3`** : modèle simple, interprétable et rapide à entraîner. Les métriques locales observées sont recall `0.728`, précision `0.562` et accuracy `0.886` sur le jeu v1 courant.
2. **Régression logistique avec d'autres valeurs de `C` ou seuils** : permet d'ajuster la régularisation ou d'augmenter le recall en abaissant le seuil.
3. **Forêt aléatoire** : peut mieux modéliser des relations non linéaires, mais nécessite plus de ressources et peut être moins facile à expliquer.

## Décision

Choisir la régression logistique avec le seuil d'alerte `0.2` dans la mesure où ce réglage offre le meilleur recall observé sur la version v1 : `0.838`, contre `0.750` pour la régression logistique au seuil `0.3`. La précision obtenue est `0.543`, tandis que l'accuracy est `0.882`. Cette perte de précision est acceptée au vu de la priorité donnée à la détection des pannes.

Le choix final reprend l'identifiant complet du run MLflow retenu et l'empreinte des données utilisées :

- **Modèle retenu :** régression logistique (`logreg`).
- **Seuil retenu :** `0.2`.
- **Run MLflow retenu :** `f1c451c788974128ab08b3d50ba98e38`.
- **data_md5 :** `73e0b7cb3c6f795c70c3ddf970b99c15` (8 premiers caractères : `73e0b7cb`).

## Conséquences

- La décision priorise la détection des pannes, même au prix d'un risque plus élevé de fausses alertes.
- Chaque entraînement devra rester traçable dans MLflow avec les paramètres, les métriques et `data_md5`.
- Le modèle devra être réévalué lorsque les données réelles remplaceront les données synthétiques ou lorsqu'une nouvelle version des données sera utilisée.
- Avant livraison, il faudra figer la version des bibliothèques, l'artefact du modèle et la version exacte des données afin de garantir la reproductibilité.
