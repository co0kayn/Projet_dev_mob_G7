# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** G7  ·  **Membres :** Ayoub Lafdaigui  ·  **Date :** 26/11/2026

> Toutes les sorties ci-dessous viennent d'une exécution réelle le 26/11/2026, sur le starter `S8-tp6`
> (Docker Desktop 4.99.0, Python 3.13 en local, image `python:3.11-slim`). Aucune clé API n'est reproduite ici.

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```
Hello from Docker!
Client:
 Version:           29.9.3
Server: Docker Desktop 4.99.0 (245822)
  Version:          29.9.3
```

Dernière ligne de `python -m pytest` après la mise en place (starter inchangé, avant tout Dockerfile) :

```
5 failed, 33 passed, 4 warnings in 37.54s
```

Les cinq échecs sont bien ceux de `tests/test_docker.py` : `test_dockerfile_installs_libraries_before_copying_the_code`,
`test_api_listens_on_all_interfaces`, `test_secrets_data_and_models_stay_out_of_the_image`,
`test_compose_mounts_the_model_and_names_the_api` et `test_ui_reads_the_api_url_from_the_environment`.

## 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?
   L'image est le résultat figé et nommé du Dockerfile (système, Python, bibliothèques, code) ; elle ne tourne pas.
   Un conteneur est une instance de cette image en cours d'exécution, isolée (ses fichiers, son réseau, ses
   processus). On peut lancer autant de conteneurs qu'on veut à partir de la même image.
2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
   Chaque instruction crée une couche, et Docker réutilise toutes les couches jusqu'à la première qui change.
   Les bibliothèques (installation lente, changent rarement) passent avant le code (change souvent) : modifier
   le code ne relance donc pas le `pip install`.
3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?
   Le modèle a été entraîné et sérialisé avec cette version ; une autre peut refuser de le charger ou prédire
   différemment. Figer la version rend aussi l'image reproductible : deux builds donnent les mêmes bibliothèques.
4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
   L'image sert le modèle (API et interface) : on n'y entraîne pas, on n'y versionne pas les données et on n'y
   teste pas. Ces outils alourdiraient l'image et le build sans servir à l'exécution.

## 3. Sprint 1 : le Dockerfile

Mon `Dockerfile` (fichier [Dockerfile](Dockerfile)) :

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
| premier build (`docker build --no-cache`) | 169,3 s (2 min 49 s), dont `RUN pip install` 90,5 s | 1.13 GB (contenu compressé : 259 MB) |
| après une modification de `maintai/predict.py` | 26,1 s | 1.13 GB |

Que signifie `CACHED` dans le journal du second build ?

Docker a réutilisé la couche déjà construite au lieu de réexécuter l'instruction : `WORKDIR`,
`COPY requirements-docker.txt` et `RUN pip install` sont `CACHED`, car rien n'a changé avant eux. Seules les
couches à partir de `COPY maintai` (le fichier modifié) sont reconstruites ; le `pip install` de 90 s n'est pas
rejoué. Sur ma machine, le second build reste à 26 s parce que la couche `COPY maintai` a pris 16,6 s à elle seule.

## 4. Sprint 1 : lancer un conteneur

Ma commande `docker run`, lancée depuis `TP6` (cmd : `%cd%` ; PowerShell : `${PWD}`) :

```
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "%cd%\models:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse |
|---|---|
| `GET /health` | 200 `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` sans clé | 401 `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict` avec la clé | 200 `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-11-26T21:09:42Z"}` |

Relevé envoyé : `{"temperature_c":72.5,"vibration_mm_s":6.1,"load_pct":85.0,"runtime_hours":15000}`.
Le `releve.json` fourni dans le starter contient `"temperature_c": 500` : l'API le refuse avec un 422
(`Input should be less than or equal to 150`), donc je ne l'ai pas utilisé.

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

`/health` répond 200 `{"status":"ok","model_loaded":false}` et `/v1/predict` (avec la clé et un relevé valide)
répond 503 `{"detail":"Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API"}`. Le modèle
n'est pas dans l'image (`models/` est exclu par `.dockerignore`) : sans le volume, `/app/models` est vide. L'API
démarre quand même, mais n'a aucun modèle à charger.

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

`docker logs test` affiche `Application startup complete.` puis `Uvicorn running on http://127.0.0.1:8000`, donc
tout semble normal. Mais `curl http://localhost:8002/health` ne reçoit aucune réponse (réponse vide, curl code 52,
pas de code HTTP). Dans un conteneur, `127.0.0.1` veut dire « ce conteneur seulement » : les requêtes que Docker
fait suivre depuis le PC (port 8002) arrivent sur l'interface réseau du conteneur, où personne n'écoute. Il faut
écouter partout : `--host 0.0.0.0`.

## 5. Sprint 2 : Docker Compose

Mon `compose.yaml` (fichier [compose.yaml](compose.yaml)) :

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

Modification de `ui/app.py` (sprint 2, étape 2) : l'URL par défaut de la barre latérale vient de l'environnement.

```python
url = st.text_input("URL de l'API", os.getenv("MAINTAI_API_URL", "http://localhost:8000"))
```

Sortie de `docker compose ps` :

```
NAME        IMAGE           COMMAND                  SERVICE   CREATED         STATUS         PORTS
tp6-api-1   maintai:0.4.0   "uvicorn maintai.api…"   api       6 seconds ago   Up 4 seconds   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
tp6-ui-1    maintai:0.4.0   "python -m streamlit…"   ui        5 seconds ago   Up 4 seconds   0.0.0.0:8501->8501/tcp, [::]:8501->8501/tcp
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

`http://api:8000`. Elle vient de la variable d'environnement `MAINTAI_API_URL`, définie dans `compose.yaml` pour
le service `ui` et lue par `ui/app.py` avec `os.getenv("MAINTAI_API_URL", "http://localhost:8000")`.

Prédiction faite par l'interface lancée par Compose : j'ai exécuté le vrai `ui/app.py` dans le conteneur `ui`
avec le banc d'essai de Streamlit (`AppTest`), contre l'API du conteneur `api`, avec les valeurs par défaut du
formulaire (72 °C, 6 mm/s, 85 %, 15000 h) : sans clé, « Erreur 401 : Clé API absente ou invalide » ; avec la clé,
« Probabilité de panne 95 % » et « ALERTE : au-dessus du seuil 0.3 ». Je n'ai pas cliqué dans un navigateur ;
`http://localhost:8501` répond bien 200 depuis le PC.

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`) :

```
{"status":"ok","model_loaded":true}
httpx.ConnectError: [Errno 111] Connection refused
```

Pourquoi la seconde échoue-t-elle ?

`localhost` veut toujours dire « ce conteneur ». Depuis le conteneur `ui`, il n'y a pas d'API sur le port 8000 :
l'API tourne dans un autre conteneur. Compose met les deux services sur un même réseau (`tp6_default`) où chacun
se joint par son nom de service : `http://api:8000`. Dans le navigateur, `localhost:8000` marche car c'est le PC,
et Docker relie son port 8000 à celui du conteneur `api` (`ports: "8000:8000"`).

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
38 passed, 4 warnings in 50.55s
```

`docker compose down` arrête puis supprime les deux conteneurs (`tp6-ui-1`, `tp6-api-1`) et le réseau
`tp6_default`. Je l'ai vérifié : il ne reste aucun conteneur ni réseau `tp6`, mais l'image `maintai:0.4.0`
(1.13 GB) et les dossiers `models/` et `data/` du PC sont toujours là (montés, pas copiés).

## 6. Décision : l'ADR 005

Dans [docs/adr/005-image-docker.md](docs/adr/005-image-docker.md). En deux phrases :

L'image ne porte que le code et les bibliothèques figées ; le modèle et les données arrivent au lancement par des
volumes en lecture seule, et la clé API par `.env`. Ainsi un réentraînement ne demande pas de nouveau build, et
aucun secret ni modèle ne part avec une image partagée.

## 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément.
   Dans l'image (`docker build`) : Linux + Python 3.11 (`FROM`), les bibliothèques figées (`RUN pip install`), le
   code `maintai/` et `ui/` (`COPY`). Au lancement : le modèle `models/` (volume `-v` / `volumes:`), les données
   `data/` (volume), la clé API (`--env-file .env` / `env_file:`), l'URL de l'API pour l'interface
   (`environment:`).
2. Pourquoi la clé API n'est-elle jamais dans l'image ?
   Une image se partage (registre, collègues, serveur) et chacune de ses couches se lit : une clé dedans serait
   publiée avec elle et ne pourrait plus être changée sans reconstruire. Elle est donc exclue par `.dockerignore`
   et fournie au lancement.
3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?
   Au wheel (le code, TP4) et au modèle versionné (MLflow / DVC, TP5), Docker ajoute l'environnement d'exécution
   complet : système, version de Python, bibliothèques figées et commande de lancement. Le service tourne ainsi
   de la même façon sur tout PC ou serveur qui a Docker, sans `.venv` à préparer.

## 8. Le rendu Git

- Dépôt du groupe : https://github.com/co0kayn/Projet_dev_mob_G7 · mon dossier : `TP6/ayoub_lafdaigui`
- Lien de la pull request : À RENSEIGNER
- Le tag `tp6` existe sur GitHub : À RENSEIGNER
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` n'apparaissent pas ; seuls `COMPTE_RENDU.md`,
  `Dockerfile`, `.dockerignore`, `compose.yaml` et l'ADR 005 sont ajoutés.

## 9. Ce qui reste flou

- La taille de l'image : 1.13 GB pour une API et une interface. Un build en plusieurs étapes ou des images
  séparées pour `api` et `ui` la réduiraient-ils vraiment ?
- Le second build : 26 s alors que seules deux couches de code changent. Qu'est-ce qui coûte encore du temps
  quand tout le reste est `CACHED` (copie du contexte, export de l'image) ?
- Comment livrer l'image et le modèle sur un vrai serveur (registre d'images, copie de `models/` à part, ou DVC
  au démarrage), et comment passer la clé API plus sûrement qu'avec un fichier `.env` ?
