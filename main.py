from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import torch
import io
import logging
from src.datasets.plant_disease import get_image_transforms, PlantDataset
from src.Models.resnet import ResNet50
from typing import List
from google import genai
from google.genai import types
from fastapi.responses import StreamingResponse
app = FastAPI()

# Configure CORS
origins = [
    "*", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_model():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Loading model on device: {device}")
    
    dataset = PlantDataset(root="Plantdisease/train")
    num_classes = len(dataset.class_to_idx) 
    model = ResNet50(num_classes=num_classes).to(device)
    
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


@app.get("/")
async def index():
    return {"message": "Welcome to the Plant Disease Prediction API!"}


@app.post("/generate-stream")
async def generate_stream(request: Request):
    body = await request.json()
    user_input = body.get("input", "")

    def stream_response():
        client = genai.Client(
            vertexai=True,
            project="hexel-studio-admin",
            location="us-central1",
        )

        model = "gemini-2.5-pro-preview-05-06"
        contents = [
            types.Content(
                role="user",
                parts=[types.Part(text=user_input)]
            )
        ]
        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            max_output_tokens=8192,
            response_modalities=["TEXT"],
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
            ],
        )

        try:
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"\n[ERROR] {str(e)}"

    return StreamingResponse(stream_response(), media_type="text/plain")



@app.post("/predict/")
async def predict_images(files: List[UploadFile] = File(...)):
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
            
            # Get prediction scores
            scores = torch.softmax(output, dim=1)  # Apply softmax to get probabilities
            max_score, predicted = torch.max(scores, 1)  # Get the max score and class index
            
            # Check the threshold
            threshold = 0.7  # Example threshold; adjust as needed
            if max_score.item() > threshold:
                class_index = predicted.item()  # Convert the tensor to a Python integer
                class_name = idx_to_class[class_index]  # Get the class name from the index
                result = {
                    'class_index': class_index,
                    'class_name': class_name
                }
            else:
                result = {
                    'class_index': None,
                    'class_name': "Healthy image"
                }
            
            # Append result to predictions list
            predictions.append(result)
            
            logger.info(f"Processed file: {file.filename}, result: {result['class_name']}")
        
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
            predictions.append({
                'class_index': None,
                'class_name': f"Error processing file {file.filename}: {e}"
            })
    
    logger.info("Prediction completed.")
    
    # Return the predictions in a JSON response
    return JSONResponse(content={"predictions": predictions})
