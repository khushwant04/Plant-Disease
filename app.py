from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
import torch
import io
import logging
from src.datasets.plant_disease import get_image_transforms, PlantDataset
from src.Models.resnet import ResNet50

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load the model
def load_model():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Loading model on device: {device}")
    
    # Initialize the model
    dataset = PlantDataset(root="Plantdisease/train")
    num_classes = len(dataset.class_to_idx)  # Determine the number of classes
    model = ResNet50(num_classes=num_classes).to(device)
    
    # Attempt to load the checkpoint
    try:
        checkpoint = torch.load('model/final_model.pth', map_location=device)
        if 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            # Load full model if not using state_dict
            model.load_state_dict(checkpoint)
        logger.info("Model loaded successfully.")
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise RuntimeError(f"Error loading model: {e}")
    
    model.eval()  # Set model to evaluation mode
    return model

model = load_model()

# Define the image transformations
transform = get_image_transforms()

# Define the idx_to_class mapping from dataset
dataset = PlantDataset(root="Plantdisease/train")
class_to_idx = dataset.class_to_idx
idx_to_class = {idx: class_name for class_name, idx in class_to_idx.items()}

# Function to preprocess the image before inference
def preprocess_image(image):
    image = transform(image).unsqueeze(0)  # Apply transformations and add batch dimension
    return image

@app.post("/predict/")
async def predict_images(files: list[UploadFile] = File(...)):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    predictions = []
    
    logger.info("Prediction started.")
    
    for file in files:
        try:
            # Read and preprocess the uploaded image
            image = Image.open(io.BytesIO(await file.read())).convert("RGB")  # Convert to RGB
            image_tensor = preprocess_image(image).to(device)  # Apply transformations and move to device
            
            # Make a prediction
            with torch.no_grad():  # No gradient computation needed for inference
                output = model(image_tensor)  # Forward pass through the model
            _, predicted = torch.max(output, 1)  # Get the class index with the highest score
            class_index = predicted.item()  # Convert the tensor to a Python integer
            class_name = idx_to_class[class_index]  # Get the class name from the index
            
            # Append result to predictions list
            predictions.append({
                'class_index': class_index,
                'class_name': class_name
            })
            
            logger.info(f"Processed file: {file.filename}, predicted class: {class_name}")
        
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
    
    logger.info("Prediction completed.")
    
    # Return the predictions in a JSON response
    return JSONResponse(content={"predictions": predictions})
