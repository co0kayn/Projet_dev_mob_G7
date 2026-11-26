# TP6 Â· Conteneuriser MaintAI : dossier complet

**Groupe :** G7  Â·  **Auteur :** Abderrahman Erritouni

Sommaire : 1. Compte rendu Â· 2. Dockerfile Â· 3. .dockerignore Â· 4. compose.yaml Â· 5. ADR 005

---

## 1. Compte rendu (`COMPTE_RENDU.md`)

### Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** G7  ·  **Membres :** Abderrahman Erritouni  ·  **Date :** 26/11/2026, rédigé à 11h28

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP6.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

#### 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```
Hello from Docker!
Client:
 Version:           29.1.2
Server: Docker Desktop 4.54.0 (212467)
```

Dernière ligne de `python -m pytest` après la mise en place :

```
5 failed, 33 passed
```

#### 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?
   L'image est le résultat figé et nommé du Dockerfile (système, Python, bibliothèques, code) ; elle ne tourne pas.
   Un conteneur est une copie de l'image qui tourne, isolée (ses fichiers, son réseau, ses processus). On peut lancer
   autant de conteneurs qu'on veut à partir d'une même image.
2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
   Chaque instruction crée une couche, et Docker réutilise toutes les couches jusqu'à la première qui change.
   Les bibliothèques (installation lente, changent rarement) passent donc avant le code (change souvent) :
   une modification du code ne relance pas le `pip install`.
3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?
   Le modèle (`model.joblib`) a été entraîné et sérialisé avec scikit-learn 1.8.0 ; une autre version peut refuser
   de le charger ou prédire différemment. Figer la version rend aussi l'image reproductible : deux builds donnent
   les mêmes bibliothèques.
4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
   L'image sert le modèle (API et interface) : on n'y entraîne pas, on n'y versionne pas les données et on n'y teste
   pas. Ces outils alourdiraient l'image et le build sans servir en production.

#### 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY maintai ./maintai
COPY ui ./ui

ENV MAINTAI_MODELS_DIR=/app/models \
    MAINTAI_DATA_PATH=/app/data/sensors.csv

EXPOSE 8000
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Build | Durée | Taille de l'image (`docker images`) |
|---|---|---|
| premier build (`docker build --no-cache`) | 1 min 44 s (104 s) | 1.13 GB |
| après une modification de `maintai/predict.py` | 1,0 s | 1.13 GB |

Que signifie `CACHED` dans le journal du second build ?

Docker a réutilisé la couche déjà construite au lieu de réexécuter l'instruction : `FROM`, `WORKDIR`,
`COPY requirements-docker.txt` et `RUN pip install` sont `CACHED` car rien n'a changé avant eux. Seules les couches
à partir de `COPY maintai` (le fichier modifié) sont reconstruites, d'où 1 s au lieu de 5 min.

#### 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` (PowerShell : `${PWD}` ; dans cmd : `%cd%`) :

```
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "${PWD}\models:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse |
|---|---|
| `GET /health` | 200 `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` sans clé | 401 `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict` avec la clé | 200 `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-11-26T10:49:08Z"}` |

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

`/health` répond `{"status":"ok","model_loaded":false}` et `/v1/predict` (avec la clé) répond 503
« Modèle non chargé ». Le modèle n'est pas dans l'image (exclu par `.dockerignore`) : sans le volume, le dossier
`/app/models` du conteneur est vide. L'API démarre quand même, mais n'a aucun modèle à charger.

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

Les journaux disent que tout va bien : `Uvicorn running on http://127.0.0.1:8000`. Mais `http://localhost:8002/health`
ne répond pas (connexion coupée, réponse vide). Dans un conteneur, 127.0.0.1 veut dire « ce conteneur seulement » :
les requêtes que Docker fait suivre depuis le PC (port 8002) arrivent sur l'interface réseau du conteneur, où
personne n'écoute. Il faut écouter partout : `--host 0.0.0.0`.

#### 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

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
    command: ["python", "-m", "streamlit", "run", "ui/app.py",
              "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
    environment:
      MAINTAI_API_URL: http://api:8000
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro
    depends_on:
      - api
```

Sortie de `docker compose ps` :

```
NAME        IMAGE           COMMAND                  SERVICE   CREATED          STATUS          PORTS
tp6-api-1   maintai:0.4.0   "uvicorn maintai.api…"   api       20 seconds ago   Up 20 seconds   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
tp6-ui-1    maintai:0.4.0   "python -m streamlit…"   ui        20 seconds ago   Up 20 seconds   0.0.0.0:8501->8501/tcp, [::]:8501->8501/tcp
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

`http://api:8000`. Elle vient de la variable d'environnement `MAINTAI_API_URL`, définie dans `compose.yaml` pour le
service `ui` et lue par `ui/app.py` avec `os.getenv("MAINTAI_API_URL", "http://localhost:8000")`.

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`). Pourquoi la seconde échoue-t-elle ?

```
{"status":"ok","model_loaded":true}
httpx.ConnectError: [Errno 111] Connection refused
```

`localhost` veut toujours dire « ce conteneur ». Depuis le conteneur `ui`, il n'y a pas d'API sur le port 8000 :
l'API tourne dans un autre conteneur. Compose met les deux services sur un même réseau (`tp6_default`) où chacun se
joint par son nom : `http://api:8000`. Dans le navigateur, `localhost:8000` marche car c'est le PC, et Docker relie le
port 8000 du PC à celui du conteneur `api` (`ports: "8000:8000"`).

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
38 passed, 4 warnings in 17.14s
```

`docker compose down` arrête et supprime les conteneurs des services (`tp6-api-1`, `tp6-ui-1`) et le réseau
`tp6_default`. Elle ne supprime ni l'image `maintai:0.4.0`, ni les dossiers `models/` et `data/` du PC
(montés, pas copiés).

#### 6. Décision : l'ADR 005

Dans `docs/adr/005-image-docker.md`. Résumez ici votre décision en deux phrases :

L'image ne porte que le code et les bibliothèques ; le modèle et les données arrivent au lancement par des volumes
en lecture seule, et la clé par `.env`. Ainsi un réentraînement ne demande pas de nouveau build, et aucun secret ni
modèle ne part avec une image partagée.

#### 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément.
   Dans l'image (`docker build`) : Linux + Python 3.11 (`FROM`), les bibliothèques figées (`RUN pip install`),
   le code `maintai/` et `ui/` (`COPY`). Au lancement : le modèle `models/` (volume `-v` / `volumes:`), les données
   `data/` (volume), la clé API (`--env-file .env` / `env_file:`), l'URL de l'API pour l'interface (`environment:`).
2. Pourquoi la clé API n'est-elle jamais dans l'image ?
   Une image se partage (registre, collègues, serveur) et chaque couche se lit : une clé dedans serait publiée avec
   elle et ne pourrait plus être changée sans reconstruire. Elle est donc exclue par `.dockerignore` et donnée au
   lancement.
3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?
   Au wheel (code, TP4) et au modèle versionné (MLflow / DVC, TP5), Docker ajoute l'environnement d'exécution
   complet : système, version de Python et bibliothèques figées, plus la commande de lancement. Le modèle tourne
   ainsi de la même façon sur tout PC ou serveur qui a Docker, sans `.venv` à préparer.

#### 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp6` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? oui / non

#### 9. Ce qui reste flou

- Comment livrer l'image et le modèle sur un vrai serveur : faut-il pousser l'image dans un registre
  (Docker Hub, GitHub Container Registry) et copier le dossier `models/` à part, ou le récupérer avec DVC au démarrage ?
- La taille de l'image (1,13 Go) : quelles pistes pour la réduire (build multi-étapes, moins de bibliothèques
  dans l'image de l'API, image séparée pour l'interface) ?
- Comment passer la clé API en production de façon plus sûre qu'un fichier `.env` (secrets Docker, variables du
  serveur) ?

---

## 2. Dockerfile

```dockerfile
# Image de MaintAI : le code et ses bibliothèques, sans les données ni le modèle.
# Construire : docker build -t maintai:0.4.0 .

# TODO TP6 sprint 1 : écrivez les instructions, dans cet ordre
#   1. FROM    : l'image de départ, python:3.11-slim (la même version de Python que sur vos PC)
#   2. WORKDIR : le dossier de travail dans l'image, /app
#   3. COPY    : requirements-docker.txt seul, puis RUN pip install --no-cache-dir -r requirements-docker.txt
#                (les bibliothèques AVANT le code : cette étape lente reste en cache)
#   4. COPY    : les dossiers maintai et ui
#   5. ENV     : MAINTAI_MODELS_DIR=/app/models et MAINTAI_DATA_PATH=/app/data/sensors.csv
#   6. EXPOSE 8000, puis CMD : uvicorn maintai.api.main:app, à l'écoute de toutes les adresses
#                (--host 0.0.0.0) sur le port 8000, en liste JSON : CMD ["uvicorn", "...", ...]

FROM python:3.11-slim

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY maintai ./maintai
COPY ui ./ui

ENV MAINTAI_MODELS_DIR=/app/models \
    MAINTAI_DATA_PATH=/app/data/sensors.csv

EXPOSE 8000
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 3. .dockerignore

```text
# Ce qui n'entre jamais dans l'image : lourd, local ou secret
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
.git/
dist/
build/
*.egg-info/
tests/
# TODO TP6 sprint 1 : ajoutez une ligne pour chacun
#   les données (data/), le modèle (models/), le secret (.env),
#   la base et les fichiers MLflow (mlflow.db, mlruns/), le cache DVC (.dvc/)
data/
models/
.env
mlflow.db
mlruns/
.dvc/
```

---

## 4. compose.yaml

```yaml
# MaintAI en deux conteneurs : l'API et l'interface Streamlit.
# Lancer : docker compose up --build      Arrêter : docker compose down

services:
  api:
    build: .
    image: maintai:0.4.0
    env_file: .env                     # MAINTAI_API_KEY, comme au TP2
    ports:
      - "8000:8000"                    # PC:conteneur
    # TODO TP6 sprint 2 : monter le dossier models du PC dans /app/models, en lecture seule
    #   volumes:
    #     - ./...:/app/...:ro
    volumes:
      - ./models:/app/models:ro

  # TODO TP6 sprint 2 : le service ui
  #   - la même image (maintai:0.4.0), avec une autre commande :
  #       ["python", "-m", "streamlit", "run", "ui/app.py",
  #        "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
  #   - la variable MAINTAI_API_URL : l'adresse de l'API vue depuis ce conteneur (le nom du service, port 8000)
  #   - le port 8501 publié sur le PC
  #   - le dossier data du PC monté dans /app/data, en lecture seule
  #   - depends_on : api
  ui:
    image: maintai:0.4.0
    command: ["python", "-m", "streamlit", "run", "ui/app.py",
              "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
    environment:
      MAINTAI_API_URL: http://api:8000
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro
    depends_on:
      - api
```

---

## 5. ADR 005 (`docs/adr/005-image-docker.md`)

### ADR 005 : le modèle arrive par un volume, l'image ne porte que le code

Date : 26/11/2026 · Auteurs : Abderrahman Erritouni

#### Contexte
MaintAI doit tourner sur un serveur où personne ne prépare de `.venv` : on l'emballe dans une image Docker
(`maintai:0.4.0`). Il faut décider ce qui entre dans l'image et ce qui arrive au lancement, en particulier
le modèle (`models/model.joblib`), qui est réentraîné plus souvent que le code ne change (TP5, MLOps).

#### Options étudiées
1. **Modèle dans l'image** (`COPY models ./models`) :
   - gagne : une image autonome, un seul artefact à livrer, code et modèle toujours cohérents ;
   - perd : chaque réentraînement impose un nouveau build et une nouvelle version d'image ; l'image grossit ;
     un modèle (et ses données d'entraînement implicites) part avec toute image partagée.
2. **Modèle par un volume** (`-v ./models:/app/models:ro`, `volumes:` dans `compose.yaml`) :
   - gagne : on change de modèle sans reconstruire ni redéployer le code ; image plus légère et réutilisable ;
     lecture seule (`:ro`), le conteneur ne peut pas abîmer le modèle ;
   - perd : l'image seule ne suffit pas, il faut fournir le dossier `models/` au lancement ; si on l'oublie,
     l'API démarre mais `/health` dit `model_loaded: false` et `/v1/predict` répond 503 (vérifié, piège 1).

#### Décision
Option 2 : le modèle et les données arrivent par des volumes en lecture seule, la clé par `--env-file .env` /
`env_file:`. Raison principale : le modèle change sans nouveau code (séance 7) ; le lier à l'image obligerait
à reconstruire pour chaque réentraînement. C'est la même règle que le wheel du TP4 : le paquet porte le code,
pas le modèle.

`.dockerignore` laisse dehors :
- `data/`, `models/` : arrivent par volume (raison ci-dessus) ;
- `.env` : un secret n'entre jamais dans une image qu'on peut partager ;
- `mlflow.db`, `mlruns/`, `.dvc/` : suivi et versionnement de l'entraînement, inutiles pour servir le modèle ;
- `.venv/`, `tests/`, `.git/`, caches, `build/`, `dist/` : lourds ou locaux, l'image installe ses propres
  bibliothèques depuis `requirements-docker.txt`.
L'autre option (tout copier) ferait gagner un `COPY .` plus simple, mais perdre en taille, en temps de build
(contexte envoyé à chaque build) et en sécurité (clé dans l'image).

#### Conséquences
- Facilite : réentraîner puis redémarrer le conteneur suffit ; une seule image pour tous les modèles.
- Rend plus difficile : déployer exige de livrer aussi `models/` (et `.env`) à côté de l'image.
- À surveiller : la compatibilité entre le modèle monté et les bibliothèques de l'image (scikit-learn figé
  à 1.8.0 dans `requirements-docker.txt`) ; `/health` doit être vérifié après chaque lancement.
