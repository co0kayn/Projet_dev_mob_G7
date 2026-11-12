# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** ·  **Membres :**SAFAA HASSANI  ·  **Date :** 12/11/2026
---

## 1. Mise en place

Résultat initial, avant correction de l’interface :
```
2 failed, 21 passed, 1 warning
```

Résultat final après correction, avec `python -m pytest -q` :
```
23 passed, 1 warning in 9.03s
```
(.venv) PS C:\Users\DELL\Downloads\TP3\maintai-starter-tp3> pytest  
======================== test session starts ========================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\DELL\Downloads\TP3\maintai-starter-tp3
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.16.0
collected 23 items                                                   

tests\test_api.py .......                                      [ 30%]
tests\test_client.py ...                                       [ 43%]
tests\test_data.py ...                                         [ 56%]
tests\test_security.py .....                                   [ 78%]
tests\test_train.py ...                                        [ 91%]
tests\test_ui.py ..                                            [100%]

========================= warnings summary ==========================
.venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\DELL\Downloads\TP3\maintai-starter-tp3\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=================== 23 passed, 1 warning in 7.23s ===================

Quels fichiers de tests échouaient initialement, et quelle erreur donnaient-ils ?
Les deux échecs concernaient `tests/test_ui.py` : `test_ui_shows_the_data` échouait car Altair refusait les intervalles de `pd.cut` comme catégories (`invalid value for 0`). `test_ui_shows_the_prediction` échouait en cascade, car le plantage du graphique empêchait la création du bouton « Prédire » (`IndexError: list index out of range`). Après conversion des intervalles en libellés texte, les 23 tests passent. Le seul avertissement restant concerne la dépréciation de `httpx` avec `starlette.testclient`.

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```
Avec `.venv` activé, cette commande doit également lancer l’interface. Sans l’environnement activé, Windows peut indiquer que `streamlit` n’est pas reconnu ou utiliser une autre installation. Aucun message exact de cette première commande n’a été enregistré pendant le TP.
```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

`python -m streamlit` lance le module Streamlit avec le Python actuellement sélectionné. Après activation de `.venv`, il utilise donc les dépendances installées pour ce projet. Les deux commandes ne sont comparables que si elles utilisent le même environnement.

## 3. Sprint 1 : l'onglet « Données »

Votre code de l'onglet « Données » (de `c1, c2, c3 = ...` jusqu'au nuage de points) :

```python
indicateurs = st.columns(3)
indicateurs[0].metric("Relevés", f"{len(df)}")
indicateurs[1].metric("Taux de panne", f"{df['failure'].mean():.1%}")
indicateurs[2].metric("Température moyenne", f"{df['temperature_c'].mean():.1f} °C")

variable = st.selectbox("Variable à analyser", FEATURES)
taux_par_tranche = (
      df.groupby(pd.cut(df[variable], bins=10), observed=False)["failure"]
      .mean()
      .dropna()
      .rename("Taux de panne")
)
taux_par_tranche.index = taux_par_tranche.index.astype(str)
st.bar_chart(taux_par_tranche)

donnees_nuage = df.assign(etat=df["failure"].map({0: "Normal", 1: "Panne"}))
st.scatter_chart(
      donnees_nuage,
      x="temperature_c",
      y="vibration_mm_s",
      color="etat",
)
```

| Indicateur | Valeur affichée |
|---|---|
| Relevés | 5 000 |
| Taux de panne | 13,6 % |
| Température moyenne | 59,8 °C |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

Le taux de panne augmente globalement lorsque la vibration augmente : dans ces données synthétiques, les vibrations élevées sont associées à un risque de panne supérieur.

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

Streamlit réexécute le script de haut en bas après une interaction avec un widget; `print("relance")` apparaît donc de nouveau dans le terminal. Les composants sont reconstruits à chaque interaction.

À quoi sert `@st.cache_data` sur la fonction `charger` ?

`@st.cache_data` mémorise le résultat de `charger` pour les mêmes arguments, afin d’éviter de relire et reparser le CSV à chaque relance du script.

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
def predict(self, reading: dict) -> dict:
      """Envoie un relevé ; lève APIError si l'API refuse, httpx.HTTPError si elle est injoignable."""
      headers = {"X-API-Key": self.api_key} if self.api_key else {}
      response = self.http.post("/v1/predict", json=reading, headers=headers)
      if response.status_code != 200:
         payload = response.json()
         detail = payload.get("detail", payload) if isinstance(payload, dict) else payload
         raise APIError(response.status_code, detail)
      return response.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
23 passed, 1 warning
```

Avec l'API lancée (`uvicorn maintai.api.main:app --reload --env-file .env`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | Probabilité de panne : 95 % (94,75 % arrondis); alerte de risque élevé. |
| valeurs par défaut, fausse clé | Erreur API avec code 401 (clé invalide). |
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) | Message « API injoignable » suivi de l’erreur de connexion HTTP. |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

Streamlit envoie la requête depuis son processus Python côté serveur, pas depuis le navigateur. CORS est une protection appliquée par les navigateurs aux requêtes JavaScript inter-origines; elle ne bloque pas une requête HTTP effectuée directement par le processus Python.

## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
   Dans le TP2, le JavaScript du navigateur envoie la requête (`fetch`). Dans Streamlit, le code Python côté serveur l’envoie avec `MaintaiClient`.
2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
   Ils injectent le client de test FastAPI (`TestClient`) dans `MaintaiClient`. La requête est traitée directement par l’application ASGI en mémoire, sans serveur réseau.
3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
   Pour une démonstration rapide à un client, je choisirais Streamlit, car les graphiques et la prédiction sont rapides à présenter. Pour un technicien, une page web dédiée conviendrait mieux à une expérience produit personnalisée et déployable largement; Streamlit convient bien à un outil interne d’analyse ou de prototypage.

## 6. Le rendu Git

- Lien de la pull request : à compléter après création de la PR.
- Le tag `tp3` existe sur GitHub : à vérifier sur le dépôt distant.
- `git status` avant le commit : non déterminé ici, car ce dossier n’est pas un dépôt Git accessible (`git status` renvoie « not a git repository »). `.gitignore` exclut `.env`, `data/*.csv` et `models/`; vérifier qu’ils ne sont pas déjà suivis dans le dépôt avant le commit.

## 7. Ce qui reste flou

À compléter avec les questions qui restent après l’exécution du TP.
