# app/config.py
import os

MODEL_PATH = os.getenv("MODEL_PATH", "model/final_model.pth")
# Only the class sub-folder names are read from here (sorted order = class index)
DATASET_PATH = os.getenv("DATASET_PATH", "Plantdisease/train")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro-preview-05-06")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "hexel-studio-admin")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# CORS settings
ORIGINS = ["*"]

# Prediction threshold
PREDICTION_THRESHOLD = 0.7
