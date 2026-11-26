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
