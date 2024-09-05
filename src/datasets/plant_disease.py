import os
import logging
from PIL import Image
import torch
from torch.utils.data import Dataset
from torchvision import transforms
from torch.utils.data import DataLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more verbose output
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Log to console
)

def get_image_transforms():
    """
    Get the transformation pipeline for image preprocessing.

    Returns:
        transforms.Compose: Composed transformation pipeline.
    """
    logging.info("Creating image transformation pipeline")
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # Resize to a fixed size
        transforms.RandomHorizontalFlip(p=0.5),  # Randomly flip horizontally
        transforms.RandomVerticalFlip(p=0.5),  # Randomly flip vertically
        transforms.RandomResizedCrop(size=224, scale=(0.8, 1.0)),  # Randomly crop and resize
        transforms.ToTensor(),  # Convert to tensor
    ])
    return transform


class PlantDataset(Dataset):
    def __init__(self, root, transform=None):
        logging.info(f"Initializing dataset from {root}")
        self.root = root
        self.transform = get_image_transforms()
        self.images = []
        self.labels = []
        self.class_to_idx = {}
        
        # Load images and labels
        for i, label_dir in enumerate(sorted(os.listdir(root))):
            class_dir = os.path.join(root, label_dir)
            self.class_to_idx[label_dir] = i
            for image_file in sorted(os.listdir(class_dir)):
                self.images.append(os.path.join(class_dir, image_file))
                self.labels.append(i)
        
        logging.info(f"Loaded {len(self.images)} images from {root}")

    def get_class_to_idx(self):
        logging.info(f"Class to index mapping: {self.class_to_idx}")
        return self.class_to_idx

    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        image_path = self.images[idx]
        logging.debug(f"Loading image: {image_path}")
        image = Image.open(image_path).convert("RGB")
        label = self.labels[idx]
        
        if self.transform:
            logging.debug(f"Applying transforms to image: {image_path}")
            image = self.transform(image)
        return image, label


def dataloaders(ROOT_DIR, BATCH_SIZE, NUM_WORKER):
    logging.info(f"Creating dataloaders with BATCH_SIZE={BATCH_SIZE} and NUM_WORKER={NUM_WORKER}")
    
    train_data = PlantDataset(ROOT_DIR + "/train", transform=get_image_transforms())
    test_data = PlantDataset(ROOT_DIR + "/test", transform=get_image_transforms())
    valid_data = PlantDataset(ROOT_DIR + "/valid", transform=get_image_transforms())

    train_loader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKER)
    test_loader = DataLoader(test_data, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKER)
    valid_loader = DataLoader(valid_data, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKER)
    
    num_classes = len(train_data.class_to_idx)
    logging.info(f"Number of classes: {num_classes}")
    
    return train_loader, test_loader, valid_loader, num_classes
