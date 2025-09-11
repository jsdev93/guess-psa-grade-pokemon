# ml_starter.py
"""
Starter script for training a PSA grade prediction model from card images.
- Uses PyTorch and torchvision
- Expects a folder structure: dataset/<grade>/<images>
- Single image input (front only) for simplicity
"""
import os
import torch
import torchvision
from torchvision import transforms, datasets, models
from torch.utils.data import DataLoader
from torch import nn, optim

# Config
DATA_DIR = 'dataset'  # Change to your dataset path
BATCH_SIZE = 16
NUM_EPOCHS = 5
NUM_CLASSES = 10  # PSA grades 1-10
IMG_SIZE = 224

# Data transforms
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
])

dataset = datasets.ImageFolder(DATA_DIR, transform=transform)
loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

# Model: ResNet18
model = models.resnet18(pretrained=True)
model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)

# Optimizer and loss
optimizer = optim.Adam(model.parameters(), lr=1e-4)
criterion = nn.CrossEntropyLoss()

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

# Training loop
for epoch in range(NUM_EPOCHS):
    model.train()
    total_loss = 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * images.size(0)
    avg_loss = total_loss / len(dataset)
    print(f"Epoch {epoch+1}/{NUM_EPOCHS} - Loss: {avg_loss:.4f}")

# Save model
os.makedirs('models', exist_ok=True)
torch.save(model.state_dict(), 'models/psa_grade_resnet18.pth')
print('Model saved to models/psa_grade_resnet18.pth')

# Inference example
# img = Image.open('some_card.jpg')
# x = transform(img).unsqueeze(0).to(device)
# model.eval()
# with torch.no_grad():
#     pred = model(x).argmax(dim=1).item() + 1  # +1 if your folders are 0-indexed
# print('Predicted grade:', pred)
