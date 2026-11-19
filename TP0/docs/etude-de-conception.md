

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
