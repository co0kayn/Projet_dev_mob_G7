# ADR 000 : Choix du modèle et du seuil d'alerte de MaintAI

Date : 19/11/2026 · Auteurs : [noms]

## Contexte
MaintAI doit prévenir les pannes de machines à partir de quatre capteurs (température, vibration, charge, heures de fonctionnement). Les pannes sont rares (13,6 % des relevés : la baseline « jamais de panne » a 86,4 % d'accuracy et 0 % de recall), et **une panne manquée coûte plus cher qu'une fausse alerte**. Il faut donc choisir le modèle et le seuil en regardant d'abord le **recall**, pas l'accuracy.

Données utilisées : `data/sensors.csv` v1, 5 000 lignes (4 000 entraînement / 1 000 test), `data_md5 = 73e0b7cb3c6f795c70c3ddf970b99c15`.

## Options étudiées
Runs MLflow, expérience `maintai`, mêmes données :

| Run | Modèle | C | Seuil | recall | precision | accuracy |
|---|---|---|---|---|---|---|
| `b3b93324` | logreg | 1.0 | 0.3 | 0.750 | 0.622 | 0.904 |
| `ecf96e36` | logreg | 0.01 | 0.3 | 0.691 | 0.653 | 0.908 |
| `bdafb172` | logreg | 1.0 | **0.2** | **0.838** | 0.543 | 0.882 |
| `9a0c4aaa` | forest (200 arbres) | – | 0.3 | 0.728 | 0.562 | 0.886 |
| `e84c84f2` | forest (200 arbres) | – | 0.2 | 0.831 | 0.479 | 0.854 |

1. **Régression logistique, C = 1.0, seuil 0.3** (réglage par défaut). Avantages : la meilleure accuracy, une precision correcte, un modèle simple et rapide. Inconvénients : elle manque 25 % des pannes.
2. **Régression logistique, C = 0.01** (plus de régularisation). Avantages : la meilleure precision (moins de fausses alertes). Inconvénients : le plus mauvais recall (31 % de pannes manquées), ce qui ne colle pas à la contrainte métier.
3. **Régression logistique, C = 1.0, seuil 0.2**. Avantages : le meilleur recall (83,8 %), avec une precision qui reste acceptable (54 % des alertes sont de vraies pannes). Inconvénients : plus de fausses alertes, donc plus d'interventions inutiles.
4. **Random forest, seuil 0.3 ou 0.2**. Avantages : peut capter des relations non linéaires. Inconvénients : à seuil égal, elle fait moins bien que la régression logistique sur le recall **et** sur la precision. Le modèle est aussi plus lourd, moins lisible, et il faut déclarer des types de confiance (`skops_trusted_types`) pour le sauvegarder.

## Décision
On retient la **régression logistique (C = 1.0) avec un seuil d'alerte de 0.2**. C'est le run MLflow **`bdafb172049c4f9e87f6561dd1e0f72d`**, entraîné sur les données **`data_md5 = 73e0b7cb…`** (v1).
Raison principale : c'est le meilleur recall de tous les essais (0.838 contre 0.750 au seuil par défaut). Comme une panne manquée coûte plus cher qu'une fausse alerte, on accepte de perdre un peu de precision (0.543) et d'accuracy (0.882, ce qui reste au-dessus de la baseline à 0.864). La random forest n'apporte aucun gain qui justifierait sa complexité.

## Conséquences
- **Ce qui est plus facile** : le modèle est simple, rapide et explicable (on peut lire les coefficients). Le run MLflow fige la version de scikit-learn (1.8.0) et des dépendances, et `data_md5` relie le modèle à la version exacte des données suivie par DVC. N'importe qui peut donc reproduire le modèle.
- **Ce qui est plus difficile** : il y aura plus de fausses alertes (environ une alerte sur deux est fausse). Les équipes de maintenance doivent en être prévenues pour ne pas finir par ignorer les alertes.
- **Ce qu'il faut configurer** : il faut entraîner avec `--threshold 0.2` (ou `MAINTAI_THRESHOLD=0.2`), sinon c'est la valeur par défaut 0.3 qui s'applique. Le seuil est écrit dans `models/model_info.json` et l'API le lit à cet endroit.
- **Ce qu'il faut surveiller** : le recall en production, et le rapport fausses alertes / pannes évitées. Si les données changent (nouvelle version DVC, nouveau `data_md5`), il faut refaire la comparaison avec les mêmes réglages avant de garder cette décision.
