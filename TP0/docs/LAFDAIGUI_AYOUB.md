# TPO : CantineAI

**Nom :** LAFDAIGUI AYOUB  
**Groupe :** 5IAD G1  

## Problématique

L’objectif est de prévoir le nombre de repas à commander pour le lendemain à partir des informations disponibles la veille, notamment :

- le jour de la semaine ;
- le nombre d’élèves inscrits ;
- le menu prévu ;
- les conditions météorologiques ;
- la présence éventuelle d’examens ou de sorties scolaires ;
- la proximité des vacances ;
- le nombre de repas servis le même jour de la semaine précédente.

Une estimation trop élevée peut entraîner du gaspillage alimentaire, tandis qu’une estimation trop faible peut provoquer un manque de repas pour les élèves.

## Résultats obtenus sur le jeu de test

L’évaluation a été réalisée sur les jours les plus récents du jeu de données, selon un découpage chronologique.  

La **MAE** correspond à l’écart absolu moyen entre le nombre de repas prévus et le nombre de repas réellement servis. Elle permet donc d’estimer le nombre moyen d’erreurs de prévision.

| Modèle | MAE | RMSE | R² |
|---|---:|---:|---:|
| Régression linéaire | 22,239 | 28,170 | 0,883 |
| Forêt aléatoire | 31,845 | 41,540 | 0,746 |
| Arbre de décision | 46,000 | 59,710 | 0,475 |
| Baseline | 70,271 | 88,416 | -0,151 |

## Modèle retenu

Le modèle choisi est la **régression linéaire**, car elle obtient les meilleurs résultats sur le jeu de test, notamment la MAE la plus faible.

En moyenne, ses prévisions s’écartent d’environ **22 repas** du nombre réellement servi. À titre de comparaison, l’erreur moyenne de la baseline est d’environ **70 repas**.

La régression linéaire permet donc de réduire l’erreur absolue moyenne d’environ **68 %** par rapport à la baseline. Elle constitue ainsi le modèle le plus performant parmi ceux testés.

## Le critère de réussite est-il atteint ?

Aucun seuil chiffré d’acceptation n’a été défini dans la fiche de projet. Les résultats montrent néanmoins une amélioration importante par rapport à la baseline.

Avant de considérer le modèle comme suffisamment précis pour déterminer automatiquement les commandes, il sera nécessaire de définir avec le gestionnaire de la cantine une marge d’erreur acceptable, exprimée en nombre de repas.

## Limites et points à préciser

Plusieurs éléments doivent encore être pris en compte :

- Les données utilisées sont synthétiques. Les performances obtenues peuvent donc différer avec les données réelles de la cantine.
- Le jeu de test représente environ 20 % des 340 jours disponibles, soit près de 68 jours récents.
- La MAE ne permet pas de distinguer les repas préparés en excès des repas manquants, alors que leurs conséquences ne sont pas les mêmes.
- La marge d’erreur acceptable doit encore être définie.
- Il faut également évaluer le coût du gaspillage par rapport au coût des repas manquants.
- Le modèle devrait d’abord être suivi et évalué sur des données réelles avant d’être utilisé seul pour déterminer les quantités à commander.

## Conclusion

La régression linéaire est le modèle le plus adapté parmi ceux testés. Elle offre une amélioration nette par rapport à la baseline et réduit considérablement l’erreur moyenne de prévision.

Cependant, une phase de validation sur des données réelles reste indispensable afin de mesurer sa fiabilité et de déterminer si son niveau de précision est suffisant pour une utilisation opérationnelle dans la gestion des commandes de la cantine.