# app/utils/preprocessing.py
from src.datasets.plant_disease import get_eval_transforms

# Deterministic inference transform (the training transform applies random flips/crops)
transform = get_eval_transforms()

def preprocess_image(image):
    """Preprocess an image for model inference"""
    image = transform(image).unsqueeze(0)  # Apply transformations and add batch dimension
    return image
