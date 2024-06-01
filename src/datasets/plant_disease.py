import os
from PIL import Image
import torch
from torch.utils.data import Dataset
from torchvision import transforms


def get_image_transforms():
    """
    Get the transformation pipeline for image preprocessing.

    Returns:
        transforms.Compose: Composed transformation pipeline.
    """
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # Resize to a fixed size
        transforms.RandomHorizontalFlip(p=0.5),  # Randomly flip horizontally
        transforms.RandomVerticalFlip(p=0.5),  # Randomly flip vertically
        transforms.RandomResizedCrop(size=224, scale=(0.8, 1.0)),  # Randomly crop and resize
        transforms.ToTensor(),  # Convert to tensor
        
    ])
    return transform



class PlantDataset(Dataset):
    def __init__(self,root,transform=None):
        self.root = root
        self.transform = get_image_transforms()
        self.images = []
        self.labels = []
        self.class_to_idx = {}
        
        for i, label_dir in enumerate(sorted(os.listdir(root))):
            class_dir = os.path.join(root,label_dir)
            self.class_to_idx[label_dir] = i
            for image_file in sorted(os.listdir(class_dir)):
                self.images.append(os.path.join(class_dir,image_file))
                self.labels.append(i)
                
    
    def get_class_to_idx(self):
        return self.class_to_idx
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self,idx):
        image_path = self.images[idx]
        image = Image.open(image_path).convert("RGB")
        label = self.labels[idx]
        
        if self.transform:
            image = self.transform(image)
        return image, label
