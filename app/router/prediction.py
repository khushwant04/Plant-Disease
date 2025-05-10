# app/routers/prediction.py

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from typing import List
from PIL import Image
import torch
import io

from app.models.model_loader import model_manager
from app.utils import preprocess_image
from app.logging_config import logger
from app.config import PREDICTION_THRESHOLD

router = APIRouter()

@router.get("/")
async def index():
    return {"message": "Welcome to the Plant Disease Prediction API!"}

@router.post("/predict/")
async def predict_images(files: List[UploadFile] = File(...)):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    predictions = []

    # Load model and class mapping
    model = model_manager.get_model().to(device)
    model.eval()
    idx_to_class = model_manager.get_idx_to_class()

    logger.info(f"Prediction started for {len(files)} images")

    for file in files:
        try:
            # Read and preprocess image
            image = Image.open(io.BytesIO(await file.read())).convert("RGB")
            image_tensor = preprocess_image(image).to(device)

            # Make prediction
            with torch.no_grad():
                output = model(image_tensor)

            # Get top 10 predictions
            scores = torch.softmax(output, dim=1)
            topk_scores, topk_indices = torch.topk(scores, k=10, dim=1)

            top_predictions = []
            for idx, score in zip(topk_indices[0], topk_scores[0]):
                class_index = idx.item()
                class_name = idx_to_class[class_index]
                top_predictions.append({
                    'class_index': class_index,
                    'class_name': class_name,
                    'confidence': float(score.item())
                })

            # Determine if top-1 prediction is above threshold
            if top_predictions[0]['confidence'] > PREDICTION_THRESHOLD:
                result = {
                    'filename': file.filename,
                    'top_predictions': top_predictions
                }
            else:
                result = {
                    'filename': file.filename,
                    'top_predictions': [{
                        'class_index': None,
                        'class_name': "Healthy image",
                        'confidence': top_predictions[0]['confidence']
                    }]
                }

            predictions.append(result)
            logger.info(f"Processed file: {file.filename}, top-1: {top_predictions[0]['class_name']}")

        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
            predictions.append({
                'filename': file.filename,
                'top_predictions': [{
                    'class_index': None,
                    'class_name': f"Error processing file: {str(e)}",
                    'confidence': 0.0
                }]
            })

    logger.info("Prediction completed.")

    return JSONResponse(content={"predictions": predictions})
