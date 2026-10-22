# Choix du modèle

Date : 22/10/2026 · NAME : ABDERRAHMAN ERRITOUNI

## Contexte
La cantine doit savoir combien de repas préparer pour un jour donné : trop peu, des élèves
ne mangent pas ; trop, la nourriture est jetée. On prédit `repas_servis` à partir du calendrier,
de la météo et de la vie de l'établissement.

Métrique principale : **MAE** (erreur absolue moyenne), exprimée directement en repas. Elle se lit
comme « on se trompe en moyenne de N repas », ce qui est le langage de la décision ; contrairement
au RMSE, elle ne surpondère pas les quelques jours très atypiques.

## Données et découpage
- Fichier : `data/cantine_repas.csv` — **340 lignes**, du 09/09/2024 au 19/06/2026, aucune ligne
  écartée (cible jamais manquante).
- Cible : `repas_servis` (moyenne 499, min 248, max 695).
- 9 colonnes d'entrée : `jour`, `inscrits`, `menu`, `temperature_c`, `pluie_mm`, `examens`,
  `sortie_scolaire`, `veille_vacances`, `repas_semaine_precedente`. La colonne `date` sert
  uniquement à ordonner les lignes.
- Découpage **chronologique** (`TEST_SIZE = 0.2`) : le modèle apprend le passé et est évalué sur
  le futur, comme en production.
  - entraînement : 272 jours, du 09/09/2024 au 24/02/2026 ;
  - test : 68 jours, du 25/02/2026 au 19/06/2026.
- Préparation : médiane + standardisation pour les colonnes numériques, mode + one-hot pour les
  catégorielles (`jour`, `menu`).

## Résultats sur le jeu de test

| Modèle | MAE (repas) ↓ | RMSE | R² |
|---|---|---|---|
| Baseline (moyenne du train) | 70.271 | 88.416 | -0.151 |
| **Régression linéaire** | **22.239** | **28.170** | **0.883** |
| Forêt aléatoire | 31.845 | 41.540 | 0.746 |
| Arbre de décision | 46.000 | 59.710 | 0.475 |

Reproductible avec `python -m monprojet.train` (graine 42) ; chiffres également dans
`models/metrics.json`.

## Décision
Modèle retenu : **la régression linéaire**.

- Elle bat la baseline de **48 repas de MAE** (70.3 → 22.2, soit **−68 %**). L'erreur moyenne passe
  d'environ 14 % à **4 % de la fréquentation moyenne** du jeu de test (524.6 repas/jour).
- Elle bat aussi les deux modèles à base d'arbres (−30 % de MAE face à la forêt aléatoire). La
  relation est donc essentiellement linéaire : c'est le modèle le plus simple **et** le plus précis,
  et en prime le plus facile à expliquer à la gestionnaire de la cantine (un coefficient par facteur).
- Le R² négatif de la baseline confirme que prédire toujours la moyenne du passé est pire que rien
  sur cette période : la fréquentation a dérivé entre l'entraînement (492.6 repas/jour en moyenne)
  et le test (524.6). Un vrai modèle est nécessaire.

Critère d'acceptation : **non défini** — la section 5 de `etude-de-conception.md` est encore vide.
À compléter avec un seuil chiffré (par exemple « MAE ≤ 25 repas sur les 68 derniers jours ») avant
de pouvoir conclure formellement.

## Limites
- **Fuite de données possible.** `repas_semaine_precedente` est la colonne la plus prédictive, mais
  rien ne garantit qu'elle est connue au moment où la commande est passée. Si elle ne l'est pas, le
  score réel sera nettement moins bon. À vérifier avant toute mise en service.
- **60 valeurs manquantes sur 340** dans cette même colonne, remplacées par la médiane : pour ces
  jours-là, le modèle travaille sur une valeur inventée.
- **Jeu de test petit et saisonnier** : 68 jours, tous entre février et juin. Rien ne dit comment le
  modèle se comporte en septembre ou en décembre.
- La MAE est une moyenne : elle **masque les jours extrêmes**. Un jour à 248 repas mal prédit coûte
  plus cher qu'une erreur de 20 repas répétée, et ces chiffres ne le montrent pas.
- Le modèle ne dit pas **dans quel sens** il se trompe. Sous-estimer (élèves sans repas) et
  surestimer (gaspillage) n'ont pas le même coût ; une analyse des résidus signés serait utile.
- Une seule exécution, une seule graine : pas d'intervalle de confiance sur ces écarts.
