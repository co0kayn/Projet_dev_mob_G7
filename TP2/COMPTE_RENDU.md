# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** …  ·  **Membres :** …  ·  **Date :** …

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP2.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Cas | Requête (corps ou URL) | Prévu | Obtenu |
|---|---|---:|---:|
| Champ manquant | `POST /v1/predict` avec `{"temperature_c":60.0,"vibration_mm_s":2.0,"runtime_hours":5000}` (champ manquant : `load_pct`) | 422 | 422 |
| Valeur absurde | `POST /v1/predict` avec `{"temperature_c":500,"vibration_mm_s":2.0,"load_pct":50.0,"runtime_hours":5000}` | 422 | 422 |
| Texte au lieu d'un nombre | `POST /v1/predict` avec `{"temperature_c":"soixante","vibration_mm_s":2.0,"load_pct":50.0,"runtime_hours":5000}` | 422 | 422 |
| Champ en trop | `POST /v1/predict` avec `{"temperature_c":60.0,"vibration_mm_s":2.0,"load_pct":50.0,"runtime_hours":5000,"pressure":2}` (champ en trop : `pressure`) | 422 | 422 |
| Mauvaise route | `POST /v1/predicte` avec `{"temperature_c":60.0,"vibration_mm_s":2.0,"load_pct":50.0,"runtime_hours":5000}` | 404 | 404 |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

Aucune : les cinq codes obtenus correspondent aux codes prévus. Les quatre requêtes invalides renvoient 422, et la route inexistante renvoie 404.

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```
19 passed, 1 warning in 2.59s
```

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

`@pytest.mark.parametrize` exécute la même fonction de test une fois pour chaque jeu de paramètres fourni. Ici, `CAS_REFUSES` contient cinq cas, donc pytest compte cinq tests pour cette fonction.

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :
help: Convert to `datetime.UTC` alias
   |
5  | import json
   - from datetime import datetime, timezone
6  + from datetime import datetime, timezone, UTC
7  |
--------------------------------------------------------------------------------
57 |         "threshold": settings.threshold,
   -         "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
58 +         "trained_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
59 |         "sklearn_version": sklearn.__version__,
   |

Found 1 error.
[*] 1 fixable with `--fix`.
(.venv) PS C:\Users\DELL\Downloads\S4_maintai-starter-tp1\maintai-starter-tp1> ruff check . --fix
Found 3 errors (3 fixed, 0 remaining).
(.venv) PS C:\Users\DELL\Downloads\S4_maintai-starter-tp1\maintai-starter-tp1> ruff format .
11 files reformatted, 7 files left unchanged
(.venv) PS C:\Users\DELL\Downloads\S4_maintai-starter-tp1\maintai-starter-tp1> ruff check . --fix
All checks passed!

Relance de `ruff check .` (sans `--fix`) depuis la racine de `TP/TP1` :

```
All checks passed!
```


Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

`ruff check .` analyse statiquement le code Python pour détecter des problèmes de style et certaines erreurs potentielles, sans exécuter l’application. `python -m pytest` exécute les tests pour vérifier le comportement du code. La sortie exacte de Ruff reste à copier après avoir lancé `ruff check .` depuis la racine de `TP/TP1`.

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
(collez ici)
```

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

…

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    api_key = get_settings().api_key

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clé API non configurée sur le serveur",
        )

    if x_api_key is None or not secrets.compare_digest(x_api_key, api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide",
        )

Votre ligne `router = ...` dans `maintai/api/main.py` :

@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API",
        )
    return PredictionOut(**predictor.predict(reading.model_dump()))

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

…

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

testpaths: tests
plugins: anyio-4.16.0
collected 18 items

tests\test_api.py .......                                                                                 [ 38%]
tests\test_data.py ...                                                                                    [ 55%]
tests\test_security.py .....                                                                              [ 83%]
tests\test_train.py ...                                                                                   [100%]

=============================================== warnings summary ===============================================
.venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\DELL\Downloads\S5_maintai-starter-tp2\maintai-starter-tp2\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================================== 18 passed, 1 warning in 2.61s =========================================




…

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

…

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
  try {
    const response = await fetch(`${url}/v1/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": key,
      },
      body: JSON.stringify(reading),
    });
    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || `Erreur HTTP ${response.status}`);
    }

    const probability = (result.failure_probability * 100).toFixed(1);
    const message = `${result.alert ? "Alerte panne" : "Aucun risque détecté"} : ${probability}% (seuil : ${(result.threshold * 100).toFixed(1)}%, modèle : ${result.model_version})`;
    show(result.alert ? "alert" : "ok", message);
  } catch (error) {
    show("err", error.message || "Impossible de contacter l'API");
  }
```

Ce qu'affiche la page (servie sur le port 5501) :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | La page affiche la probabilité, le seuil et la version du modèle, avec « Alerte panne » ou « Aucun risque détecté » selon le résultat. |
| 500 °C, bonne clé | L'API renvoie 422 car la température dépasse la limite. Le détail de validation est une liste d'objets ; avec le code actuel, la page affiche généralement `[object Object]`. |
| relevé normal, fausse clé | L'API renvoie 401 et la page affiche « Clé API absente ou invalide ». |

**Expérience CORS.** Avec la configuration locale actuelle, `http://localhost:5501` est autorisée dans `MAINTAI_CORS_ORIGINS` : la page ne devrait pas être bloquée et la console ne devrait pas afficher d'erreur CORS. Si l'origine n'est pas autorisée, la page affiche une erreur de requête (souvent `Failed to fetch`) et la console (F12) signale que la politique CORS a bloqué l'accès à la réponse.

`curl.exe` n'est pas un navigateur et n'applique pas la politique CORS. Il peut donc afficher la réponse HTTP même lorsque le navigateur interdit à une page d'une origine non autorisée d'y accéder.

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, quatre des cinq tests échouent avec 401 au lieu du 422 attendu : la vérification d'authentification du routeur est exécutée avant la validation du corps. Le test de mauvaise route passe quand même avec 404, car `/v1/predicte` ne correspond à aucune route.

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```
Avec `headers=HEADERS`, les cinq cas doivent réussir (`5 passed` si `test_casser.py` est lancé seul). Avec les 18 tests déjà présents, le total attendu est de 23 tests réussis.
```

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?
  401 signifie que l'authentification est absente ou invalide. 422 signifie que la requête est comprise, mais que ses données ne respectent pas les validations. 403 signifie que l'utilisateur est identifié, mais n'a pas l'autorisation d'effectuer l'action.
2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?
  La clé est un secret : elle ne doit pas être publiée dans le code ou Git. `.env` contient la clé locale et est ignoré par Git ; `.env.example` contient des valeurs d'exemple et peut être commité.
3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?
  Une clé dans l'URL risque d'être enregistrée dans l'historique du navigateur, les journaux ou les liens partagés. L'en-tête évite ces expositions courantes ; HTTPS protège la transmission.
4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?
  Il effectue une comparaison en temps constant afin de réduire les fuites d'information par mesure du temps de comparaison.
5. Qu'est-ce qu'une « origine » ? `http://localhost:5501` et `http://localhost:8000` sont-elles la même origine ?
  Une origine est définie par le schéma, l'hôte et le port. Ces deux URL ont des ports différents et sont donc deux origines distinctes.

## 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp2` existe sur GitHub : oui / non
- `git status` avant le commit : le fichier `.env` n'apparaissait pas, car il est ignoré par `.gitignore`.
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  À compléter avec les informations de votre pull request.

## 9. Ce qui reste flou

À compléter avec les questions qui restent floues après le TP.
