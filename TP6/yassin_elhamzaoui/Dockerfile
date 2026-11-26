# 1. Image de départ
FROM python:3.11-slim

# 2. Dossier de travail
WORKDIR /app

# 3. Installer les dépendances avant de copier le code
COPY requirements-docker.txt .
RUN pip install --no-cache-dir --index-url https://pypi.org/simple -r requirements-docker.txt \
    && python -c "import uvicorn, uvicorn.main; assert hasattr(uvicorn.main, 'main'); print('Uvicorn OK:', uvicorn.__version__)"

# 4. Copier le code de l'application
COPY maintai ./maintai
COPY ui ./ui

# 5. Variables d'environnement
ENV MAINTAI_MODELS_DIR=/app/models
ENV MAINTAI_DATA_PATH=/app/data/sensors.csv

# 6. Port et commande de démarrage
EXPOSE 8000
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
