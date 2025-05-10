import os
from tqdm import tqdm
from src.datasets.plant_disease import dataloaders
from src.Models.resnet import ResNet50
from src.train import Train
import torch
import torch.nn as nn

# Setting device
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")

# Data Loader parameters
ROOT_DIR = "Plantdisease"
BATCH_SIZE = 128
NUM_WORKER = 4

# Loading the dataset
train_loader, test_loader, valid_loader, num_classes = dataloaders(ROOT_DIR, BATCH_SIZE, NUM_WORKER)

# Model initialization
model = ResNet50(num_classes).to(device)

# Hyperparameters
EPOCHS = 20
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(params=model.parameters(), lr=0.0001)

# Trainer initialization
trainer = Train(
    model=model,
    train_loader=train_loader,
    test_loader=valid_loader,
    loss_fn=loss_fn,
    optimizer=optimizer,
    device=device,
)

# Function to save checkpoints in the specified folder
def save_checkpoint(epoch, model, optimizer, folder="checkpoints"):
    # Ensure the folder exists
    if not os.path.exists(folder):
        os.makedirs(folder)

    checkpoint_path = os.path.join(folder, f"checkpoint-epoch-{epoch+1}.pth")
    
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
    }
    torch.save(checkpoint, checkpoint_path)
    print(f"Checkpoint saved at {checkpoint_path}")

# Function to load checkpoints
def load_checkpoint(model, optimizer, path="checkpoints/checkpoint.pth"):
    checkpoint = torch.load(path)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    start_epoch = checkpoint['epoch'] + 1
    print(f"Resuming from epoch {start_epoch}")
    return start_epoch

def train_model(resume=False, checkpoint_path=None):
    start_epoch = 0
    
    # If resume is True, load the checkpoint
    if resume and checkpoint_path:
        start_epoch = load_checkpoint(model, optimizer, checkpoint_path)
    
    # Training loop
    for epoch in range(start_epoch, EPOCHS):
        print(f"\nEpoch {epoch + 1}/{EPOCHS}")
        
        # Add tqdm for progress bar on batches
        progress_bar = tqdm(enumerate(train_loader), total=len(train_loader), desc="Training")
        
        # Train for one epoch
        for batch_idx, (inputs, targets) in progress_bar:
            # Perform a single training step
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = loss_fn(outputs, targets)
            loss.backward()
            optimizer.step()

            # Update tqdm progress bar with loss
            progress_bar.set_postfix(loss=loss.item())
        
        # Save checkpoint after each epoch
        save_checkpoint(epoch, model, optimizer, folder="checkpoints")
    
    # Save final model
    torch.save(model.state_dict(), "final_model.pth")
    print("Training completed and final model saved.")

if __name__ == "__main__":
    # Set resume=True and provide checkpoint path to resume training
    train_model(resume=False, checkpoint_path="checkpoints/checkpoint-epoch-10.pth")


