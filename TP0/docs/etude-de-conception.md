# Étude de conception – HealthTri : tri des demandes administratives (données fictives)
Groupe : projet 6
Nom : Hassani /Elhamzaoui / Lafdaigui/ Erritouni  · Version : brouillon · Date : 22/10/2026

## 1. Contexte et utilisateurs
- Organisation ou situation : le secrétariat d'une clinique de taille moyenne reçoit chaque jour des centaines de demandes de patients (rendez-vous, factures, certificats, rectification du dossier, réclamations), triées à la main.
- Utilisateur principal (un rôle précis) : le/la secrétaire médical(e) chargé(e) du tri de la boîte de réception.

## 2. Problème et décision
- Décision que l'utilisateur prend avec le système : à quel service envoyer chaque demande et avec quelle priorité (urgente / normale / basse).
- Fréquence : environ 300 demandes par jour, soit une décision par demande.
- Conséquence d'une erreur, et pour qui : une demande urgente classée en basse priorité retarde la prise en charge du patient. Une mauvaise orientation fait perdre du temps au personnel et agace le patient.

## 3. Approche par sous-problème
| Sous-problème | Approche (règles / ML / DL / LLM / RAG) | Pourquoi pas une approche plus simple |
|---|---|---|
| Catégorie de la demande (RDV, facture, certificat, réclamation…) | ML classique (TF-IDF + régression logistique) | Les règles par mots-clés échouent sur les formulations variées et les fautes. |
| Détection d'urgence | Règles (mots-clés d'alerte) + ML | Une règle seule rate les cas implicites. On garde la règle comme filet de sécurité. |
| Extraction des infos (date, n° de dossier, nom) | Règles / regex | Les formats sont réguliers, donc pas besoin de ML. |
| Brouillon de réponse | LLM + RAG sur la FAQ de la clinique | Les modèles de réponse fixes ne couvrent pas les cas particuliers. Le RAG limite les inventions. |

## 4. Données
| Jeu de données | Source et licence | Volume | Données personnelles ? |
|---|---|---|---|
| Demandes synthétiques (générées par script / LLM) | Générées par le groupe, libres d'usage | 2 000 demandes étiquetées | Non (noms et numéros inventés) |
| FAQ et procédures de la clinique (fictives) | Rédigées par le groupe | ~40 pages | Non |
| Jeu de test annoté à la main | Créé par le groupe | 300 demandes | Non |

## 5. Métriques, baseline et critères d'acceptation
- Baseline et son résultat : tri par mots-clés, exactitude de 62 % sur le jeu de test (à mesurer).
- Métrique principale et pourquoi : le rappel sur la classe « urgent », car manquer une urgence est l'erreur la plus grave. On suit aussi le F1 macro pour les catégories.
- Critères d'acceptation : rappel « urgent » ≥ 95 % et F1 macro ≥ 85 % sur le jeu de test de 300 demandes. Aucune demande urgente ne doit être classée « basse priorité ».

## 6. Architecture prévue (après la séance 5)
Demande (formulaire/mail fictif) → prétraitement → classifieur de catégorie + détecteur d'urgence → file de tâches triée → interface secrétaire (validation humaine) → journal des décisions. Le module RAG/LLM produit un brouillon de réponse que la secrétaire valide avant envoi.

## 7. Choix technologiques (après la séance 5)
| Besoin | Outil | Justification |
|---|---|---|
| Classification | Python + scikit-learn | Simple, rapide, explicable. |
| Brouillons de réponse | API LLM + base vectorielle (Chroma) | RAG sur la FAQ, léger à déployer. |
| Interface | Streamlit | Prototype rapide pour la démo. |
| Stockage et suivi | SQLite + Git | Suffisant pour un prototype. |

## 8. Risques, éthique, confidentialité
1. Les données contiennent-elles des données personnelles ? Lesquelles ? Non dans le prototype : tout est fictif. En production, il y aurait noms, coordonnées et informations de santé, soit des données sensibles au sens du RGPD. Il faudrait les anonymiser ou les pseudonymiser avant tout traitement.
2. D'où viennent les données et a-t-on le droit de les utiliser ? Elles sont générées par le groupe, sans restriction.
3. Quels biais possibles ? Le jeu synthétique peut sous-représenter certaines formulations, des fautes ou d'autres langues. On les teste explicitement.
4. Qui est affecté par une erreur ? Les patients (retard de prise en charge) et le personnel. La validation humaine reste obligatoire.
5. Le système décide-t-il seul ? Non, il propose et la secrétaire valide. Aucune décision médicale n'est automatisée.
6. Les décisions sont-elles explicables ? Oui, grâce aux mots les plus influents du modèle et aux règles d'urgence affichées.
7. Où sont envoyées les données (API externes) ? Seules des données fictives sont envoyées. En production, il faudrait un hébergement conforme (HDS) ou un modèle local.
8. Que faire en cas de panne ou de doute du modèle ? Une confiance faible renvoie la demande en tri manuel, et le tri manuel reste toujours possible.

## 9. Limites et hors périmètre
- Données fictives uniquement : aucune garantie de performance sur des demandes réelles.
- Pas de triage médical ni de diagnostic : le système traite des demandes administratives seulement.
- Pas d'intégration avec un vrai dossier patient ni de mise en production.
- Français uniquement.la règle comme filet de sécurité. |
| Extraction des infos (date, n° de dossier, nom) | Règles / regex | Les formats sont réguliers, donc pas besoin de ML. |
| Brouillon de réponse | LLM + RAG sur la FAQ de la clinique | Les modèles de réponse fixes ne couvrent pas les cas particuliers. Le RAG limite les inventions. |
