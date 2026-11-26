# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** à renseigner · **Membres :** à renseigner · **Date :** 26/11/2026

> Les valeurs indiquées comme « à renseigner » nécessitent une information du groupe ou un historique Git qui n'est pas présent dans ce dossier.

## 1. Mise en place (dans `TP/TP6`)

Première ligne de `docker run hello-world` :

```
Hello from Docker!
```

`docker version` :

```
Client 29.8.2 / Server 29.8.2 — Docker Desktop 4.95.0 (242831)
```

Résultat initial attendu après la mise en place, indiqué dans le polycopié :

```
5 failed, 33 passed
```

## 2. Image et conteneur

1. Une image est le résultat immuable de la recette Docker; un conteneur est une instance de cette image en cours d'exécution.
2. `requirements-docker.txt` est copié avant le code pour que Docker puisse réutiliser la couche lente d'installation des bibliothèques lorsque seul le code change.
3. `scikit-learn==1.8.0` fixe la version utilisée pour entraîner le modèle, afin que l'environnement d'inférence reste compatible avec lui.
4. MLflow, DVC et pytest servent au suivi, au versionnement et aux tests, pas à l'exécution de l'API ou de l'interface; ils ne sont donc pas installés dans l'image de service.

## 3. Sprint 1 : le Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir --index-url https://pypi.org/simple -r requirements-docker.txt \
    && python -c "import uvicorn, uvicorn.main; assert hasattr(uvicorn.main, 'main'); print('Uvicorn OK:', uvicorn.__version__)"

COPY maintai ./maintai
COPY ui ./ui

ENV MAINTAI_MODELS_DIR=/app/models
ENV MAINTAI_DATA_PATH=/app/data/sensors.csv

EXPOSE 8000
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Build | Durée observée | Taille (`docker images`) |
|---|---:|---:|
| Premier build consigné dans le terminal | 146,1 s | 1,16 GB |
| Après modification de `maintai/predict.py` | Non mesurée | — |

`CACHED` signifie que Docker a réutilisé une couche déjà construite, car l'instruction et ses entrées n'avaient pas changé.

## 4. Sprint 1 : lancer un conteneur

Commande utilisée :

```sh
docker run -d \
  --name maintai-api \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/models:/app/models:ro" \
  maintai:0.4.0
```

| Essai | Réponse observée |
|---|---|
| `GET /health` | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` sans clé | HTTP 401, clé absente ou invalide |
| `POST /v1/predict` avec la clé | HTTP 200, prédiction reçue |

Exemple de relevé testé (aucune clé n'est incluse dans ce compte rendu) :

```json
{"temperature_c":72.5,"vibration_mm_s":6.1,"load_pct":85.0,"runtime_hours":15000}
```

Réponse de prédiction observée :

```json
{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-11-26T09:55:46Z"}
```

**Piège 1.** Sans le volume du modèle, l'API peut répondre `{"status":"ok","model_loaded":false}` sur `/health`; une prédiction authentifiée renvoie HTTP 503 car le modèle n'est pas chargé.

**Piège 2.** Avec `--host 127.0.0.1`, Uvicorn n'écoute que sur l'interface de boucle locale du conteneur. Le port publié ne peut alors pas joindre le serveur; les logs indiquent l'adresse `127.0.0.1` et `http://localhost:8002/health` échoue.

## 5. Sprint 2 : Docker Compose

```yaml
services:
  api:
    build: .
    image: maintai:0.4.0
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models:ro

  ui:
    image: maintai:0.4.0
    command:
      [
        "python",
        "-m",
        "streamlit",
        "run",
        "ui/app.py",
        "--server.address=0.0.0.0",
        "--server.port=8501",
        "--server.headless=true",
      ]
    environment:
      MAINTAI_API_URL: http://api:8000
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro
    depends_on:
      - api
```

`docker compose ps` a montré les deux services `tp6-api-1` et `tp6-ui-1` en état `Up`, avec les ports hôte `8000` et `8501` publiés.

La barre latérale affiche `http://api:8000`, défini par `MAINTAI_API_URL` dans le service `ui`. Depuis le réseau Compose, `api` est le nom DNS du service. L'appel à `http://api:8000/health` depuis `ui` répond `{"status":"ok","model_loaded":true}`; l'appel à `http://localhost:8000/health` échoue (`ConnectError`), car `localhost` désigne le conteneur `ui` lui-même.

La prédiction a aussi été envoyée depuis l'onglet « Prédiction » de l'interface Streamlit; la réponse affichée était `0 %` et « Normal : sous le seuil 0.3 ».

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
38 passed, 6 warnings
```

## 6. Décision : l'ADR 005

La décision est de garder le code et les dépendances figées dans l'image, et de fournir le modèle et les données par des volumes en lecture seule. Cela évite de reconstruire l'image pour changer ces fichiers, mais impose de fournir des dossiers compatibles au lancement; le secret reste dans `.env`, jamais dans l'image.

ADR détaillé : [docs/adr/005-image-docker.md](docs/adr/005-image-docker.md).

## 7. Questions de compréhension

1. L'image contient Python, les bibliothèques figées et le code MaintAI. Au lancement, `models/` et `data/` sont montés en lecture seule; la clé API est fournie via `env_file: .env`.
2. La clé API n'est pas mise dans l'image pour éviter de la conserver dans une image partageable et réutilisée; elle est injectée au démarrage depuis un fichier local non versionné.
3. Docker ajoute au livrable le runtime Python, les bibliothèques compatibles, le code et une commande de démarrage reproductibles. Le modèle peut rester séparé et être fourni par volume.

## 8. Le rendu Git

- Lien de la pull request : non créé; ce dossier n'est pas dans un dépôt Git.
- Le tag `tp6` existe sur GitHub : non vérifiable; aucun dépôt distant n'est configuré ici.
- `.env`, `models/` et `data/*.csv` sont listés dans `.gitignore`; toutefois, `git status` avant commit n'est pas disponible sans dépôt Git.

## 9. Ce qui reste flou

À compléter par le groupe, si des questions restent après la démonstration et la relecture.
