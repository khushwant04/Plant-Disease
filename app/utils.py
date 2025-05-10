# app/utils/preprocessing.py
from src.datasets.plant_disease import get_image_transforms

# Get the transformations from your dataset module
transform = get_image_transforms()

def preprocess_image(image):
    """Preprocess an image for model inference"""
    image = transform(image).unsqueeze(0)  # Apply transformations and add batch dimension
    return image
