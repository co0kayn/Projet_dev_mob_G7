"""Configuration du projet : c'est le seul fichier à adapter à votre sujet."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- Vos données -------------------------------------------------------------
DATA_PATH = ROOT / "data" / "cantine_repas.csv"
TARGET = "repas_servis"                      # la colonne à prédire
FEATURES = None             # None = toutes les colonnes sauf la cible ; sinon une liste de noms
TEXT_COLUMN = None           # le nom d'une colonne de texte libre (réclamations…), sinon None

# --- Type de problème --------------------------------------------------------
TASK = "regression"          # on prédit un nombre
MAIN_METRIC = "mae"           # erreur moyenne, en repas
                             # regression : "mae", "rmse", "r2"

# --- Découpage entraînement / test -------------------------------------------
SPLIT = "chronologique"      # les jours les plus récents en test
TIME_COLUMN = "date"         # la colonne qui donne l'ordre
TEST_SIZE = 0.2              # part des données gardée pour le test
SEED = 42                    # graine : mêmes résultats à chaque lancement

MODELS_DIR = ROOT / "models"
