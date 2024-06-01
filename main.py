import streamlit as st
import torch
from src.datasets.plant_disease import get_image_transforms, PlantDataset
from PIL import Image
import io

# Load the model
model = torch.load('model/model-10-epochs.pth', map_location=torch.device('cpu'))
model.eval()

# Define the image transformations
transform = get_image_transforms()

# Define the idx_to_class mapping
dataset = PlantDataset(root="plant-disease-data/Plantdisease/train")
class_to_idx = dataset.class_to_idx
idx_to_class = {idx: class_name for class_name, idx in class_to_idx.items()}

def preprocess_image(image):
    image = transform(image).unsqueeze(0)
    return image

st.title("Plant Disease Classification")

uploaded_files = st.file_uploader("Upload Images", accept_multiple_files=True, type=["jpg", "jpeg", "png"])

if uploaded_files:
    predictions = []

    # Create a placeholder for the grid
    cols = st.columns(5)  # Create 3 columns for grid layout

    for idx, uploaded_file in enumerate(uploaded_files):
        # Read and preprocess the uploaded image
        image = Image.open(io.BytesIO(uploaded_file.read())).convert("RGB")  # Ensure image is in RGB mode
        image_tensor = preprocess_image(image)

        # Make prediction
        with torch.no_grad():
            output = model(image_tensor)
        _, predicted = torch.max(output, 1)
        class_index = predicted.item()
        class_name = idx_to_class[class_index]
        predictions.append({'class_index': class_index, 'class_name': class_name})

        # Display image and prediction in grid
        col = cols[idx % 5]  # Select column based on index
        col.image(image, caption=f"Prediction: {class_name}", use_column_width=True)

    st.write(predictions)
