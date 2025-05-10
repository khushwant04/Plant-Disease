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
    
    # Get the model and class mapping
    model = model_manager.get_model()
    idx_to_class = model_manager.get_idx_to_class()
    
    logger.info(f"Prediction started for {len(files)} images")
    
    for file in files:
        try:
            # Read and preprocess the uploaded image
            image = Image.open(io.BytesIO(await file.read())).convert("RGB")
            image_tensor = preprocess_image(image).to(device)
            
            # Make a prediction
            with torch.no_grad():
                output = model(image_tensor)
            
            # Get prediction scores
            scores = torch.softmax(output, dim=1)
            max_score, predicted = torch.max(scores, 1)
            
            # Check the threshold
            if max_score.item() > PREDICTION_THRESHOLD:
                class_index = predicted.item()
                class_name = idx_to_class[class_index]
                result = {
                    'class_index': class_index,
                    'class_name': class_name,
                    'confidence': float(max_score.item())
                }
            else:
                result = {
                    'class_index': None,
                    'class_name': "Healthy image",
                    'confidence': float(max_score.item())
                }
            
            # Append result to predictions list
            predictions.append(result)
            
            logger.info(f"Processed file: {file.filename}, result: {result['class_name']}")
        
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
            predictions.append({
                'class_index': None,
                'class_name': f"Error processing file {file.filename}: {str(e)}",
                'confidence': 0.0
            })
    
    logger.info("Prediction completed.")
    
    # Return the predictions in a JSON response
    return JSONResponse(content={"predictions": predictions})
