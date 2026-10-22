# TPO : CantineAI

**Nom :** Safaa hassani 
**Groupe :** 5IAD G1

## Le problème

Prévoir le nombre de repas à commander pour le lendemain à partir des informations connues la veille : jour, nombre d'élèves inscrits, menu, météo, examens, sorties scolaires, veille de vacances et repas servis le même jour de la semaine précédente. Une prévision trop élevée entraîne du gaspillage; une prévision trop basse peut laisser des élèves sans déjeuner.

## Résultats sur le jeu de test

Le test porte sur les jours les plus récents (découpage chronologique). L'erreur absolue moyenne (MAE) indique d'environ combien de repas la prévision se trompe, en moyenne.

| Modèle | MAE | RMSE | R² |
|---|---:|---:|---:|
| Régression linéaire | 22.239 | 28.170 | 0.883 |
| Forêt aléatoire | 31.845 | 41.540 | 0.746 |
| Arbre de décision | 46.000 | 59.710 | 0.475 |
| Baseline | 70.271 | 88.416 | -0.151 |
## Mon choix, et pourquoi

Je choisis la régression linéaire : c'est le modèle qui obtient la plus petite MAE sur le jeu de test. En moyenne, sa prévision s'écarte d'environ **22 repas** du nombre réellement servi, contre environ **70 repas** pour la baseline. Cela représente une réduction de l'erreur absolue moyenne d'environ **68 %** par rapport à la baseline.

## Le critère est-il atteint ?

La fiche ne fixe pas de seuil d'acceptation chiffré. Le modèle retenu améliore nettement la baseline, mais il faut définir avec le gestionnaire une marge acceptable en repas avant de conclure que la prévision est assez précise pour les commandes.

## Ce qui reste flou

- Les données sont synthétiques; les résultats ne garantissent pas les mêmes performances avec les données réelles de la cantine.
- Le test porte sur environ 20 % des 340 jours, soit approximativement 68 jours récents.
- La MAE ne distingue pas les repas préparés en trop des repas manquants, alors que leurs conséquences diffèrent.
- Il reste à préciser la marge d'erreur acceptable et le coût des repas manquants par rapport au gaspillage.
- Les prévisions devraient être suivies sur les données réelles avant de servir seules à fixer les commandes.
