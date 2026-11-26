# Image de MaintAI : le code et ses bibliothèques, sans les données ni le modèle.
# Construire : docker build -t maintai:0.4.0 .

# 1. Image de départ (même version de Python que sur nos PC)
FROM python:3.11-slim

# 2. Dossier de travail dans l'image
WORKDIR /app

# 3. Bibliothèques AVANT le code : cette étape lente reste en cache
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# 4. Code de l'application
COPY maintai ./maintai
COPY ui ./ui

# 5. Chemins du modèle et des données (fournis par des volumes au lancement)
ENV MAINTAI_MODELS_DIR=/app/models \
    MAINTAI_DATA_PATH=/app/data/sensors.csv

# 6. Port et commande de démarrage (0.0.0.0 : écouter sur toutes les interfaces du conteneur)
EXPOSE 8000
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
