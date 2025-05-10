# app/models/model_loader.py
import torch
from src.Models.resnet import ResNet50
from src.datasets.plant_disease import PlantDataset
from app.logging_config import logger
from app.config import MODEL_PATH, DATASET_PATH

class ModelManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = None
        self.dataset = None
        self.class_to_idx = None
        self.idx_to_class = None
        self._initialized = True
        
    def load_model(self):
        """Load the model and dataset info"""
        logger.info(f"Loading model on device: {self.device}")
        
        # Load dataset for class mappings
        self.dataset = PlantDataset(root=DATASET_PATH)
        num_classes = len(self.dataset.class_to_idx)
        self.class_to_idx = self.dataset.class_to_idx
        self.idx_to_class = {idx: class_name for class_name, idx in self.class_to_idx.items()}
        
        # Initialize and load model
        self.model = ResNet50(num_classes=num_classes).to(self.device)
        
        try:
            checkpoint = torch.load(MODEL_PATH, map_location=self.device)
            if 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            self.model.eval()  # Set model to evaluation mode
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise RuntimeError(f"Error loading model: {e}")
        
        return self.model
    
    def get_model(self):
        """Return the loaded model, loading it if necessary"""
        if self.model is None:
            self.load_model()
        return self.model
    
    def get_idx_to_class(self):
        """Return the idx_to_class mapping"""
        if self.idx_to_class is None:
            self.load_model()
        return self.idx_to_class

# Create a singleton instance
model_manager = ModelManager()
