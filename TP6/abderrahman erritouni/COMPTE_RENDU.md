# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** G7  ·  **Membres :** Abderrahman Erritouni  ·  **Date :** 26/11/2026, rédigé à 11h28

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP6.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP6`)

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

## 2. Image et conteneur (pendant le premier build)

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

## 3. Sprint 1 : le Dockerfile

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

## 4. Sprint 1 : lancer un conteneur

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

## 5. Sprint 2 : Docker Compose

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

## 6. Décision : l'ADR 005

Dans `docs/adr/005-image-docker.md`. Résumez ici votre décision en deux phrases :

L'image ne porte que le code et les bibliothèques ; le modèle et les données arrivent au lancement par des volumes
en lecture seule, et la clé par `.env`. Ainsi un réentraînement ne demande pas de nouveau build, et aucun secret ni
modèle ne part avec une image partagée.

## 7. Questions de compréhension

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

## 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp6` existe sur GitHub : oui / non
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? oui / non

## 9. Ce qui reste flou

- Comment livrer l'image et le modèle sur un vrai serveur : faut-il pousser l'image dans un registre
  (Docker Hub, GitHub Container Registry) et copier le dossier `models/` à part, ou le récupérer avec DVC au démarrage ?
- La taille de l'image (1,13 Go) : quelles pistes pour la réduire (build multi-étapes, moins de bibliothèques
  dans l'image de l'API, image séparée pour l'interface) ?
- Comment passer la clé API en production de façon plus sûre qu'un fichier `.env` (secrets Docker, variables du
  serveur) ?
