from flask import Flask, request, jsonify, render_template
import torch
from src.datasets.plant_disease import get_image_transforms,PlantDataset
from PIL import Image
import io

app = Flask(__name__)

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files[]')
    predictions = []

    for file in files:
        image = Image.open(io.BytesIO(file.read())).convert("RGB")  # Ensure image is in RGB mode
        image = preprocess_image(image)
        with torch.no_grad():
            output = model(image)
        _, predicted = torch.max(output, 1)
        class_index = predicted.item()
        class_name = idx_to_class[class_index]
        predictions.append({'class_index': class_index, 'class_name': class_name})

    return jsonify({'predictions': predictions})

if __name__ == '__main__':
    app.run(debug=True)
