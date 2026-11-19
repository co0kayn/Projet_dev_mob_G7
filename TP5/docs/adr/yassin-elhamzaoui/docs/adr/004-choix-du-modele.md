
# ADR 004 : choix du modèle et du seuil d'alerte de MaintAI

Date : 19/11/2026 · Groupe : G7 · Auteurs : Yassin Elhamzaoui

## Contexte
MaintAI doit signaler les machines proches de la panne. Une panne manquée (faux négatif) coûte bien plus cher
qu'une fausse alerte (faux positif) : un arrêt imprévu de la production contre une inspection inutile.
Le critère principal est donc le **recall**, la précision restant acceptable pour ne pas noyer
les techniciens sous les alertes. Tous les runs ont été entraînés sur la même version des données
(v1, `data_md5 = b7fec427…`, 4 000 relevés d'entraînement, 1 000 de test) et suivis dans MLflow.

## Options étudiées
| Run | Modèle | Seuil | recall | precision | accuracy |
|---|---|---|---|---|---|
| A | logreg, C=1.0 | 0,3 | 0,750 | 0,622 | 0,904 |
| B | logreg, C=0.01 | 0,3 | 0,691 | 0,653 | 0,908 |
| C | logreg, C=1.0 | **0,2** | **0,838** | 0,543 | 0,882 |
| D | forest (200 arbres) | 0,3 | 0,728 | 0,562 | 0,886 |

1. **Forêt aléatoire (D)** : moins bonne que la régression logistique à seuil égal
   (recall et précision inférieurs à A), plus lourde et moins explicable. Écartée.
2. **Régression logistique, C=0.01 (B)** : la meilleure accuracy, mais le plus faible recall :
   elle rate le plus de pannes. Écartée.
3. **Régression logistique, seuil 0,3 (A)** : bon équilibre, mais une panne sur quatre est manquée.
4. **Régression logistique, seuil 0,2 (C)** : recall 0,84 ; environ une alerte sur deux est justifiée.

## Décision
On retient la **régression logistique (C = 1.0) avec un seuil d'alerte de 0,2** (run C).
- Identifiant du run MLflow : `bdafb172049c4f9e87f6561dd1e0f72d`
- Données : `data_md5 = b7fec4274774842dc1f48202c6013490` (v1, 5 000 relevés)

La contrainte qui justifie ce choix : une panne manquée coûte plus cher qu'une fausse alerte.
Par rapport au seuil 0,3, ce réglage rattrape environ 9 pannes sur 100 supplémentaires.

## Conséquences
- Ce que l'on accepte en échange : plus de fausses alertes (précision 0,54 contre 0,62),
  donc plus d'inspections inutiles. Il faudra mesurer cette charge sur le terrain.
- Le seuil est un paramètre (`MAINTAI_THRESHOLD=0.2`) : le modifier ne demande pas de réentraîner.
- Le modèle est lié à une version précise des données (`data_md5`) : tout réentraînement sur une
  nouvelle version (v2, `31ef5ebb…`) devra être comparé sur un même jeu de test avant de remplacer ce choix.
- Le modèle enregistré dans MLflow embarque ses dépendances exactes (scikit-learn 1.8.0).
