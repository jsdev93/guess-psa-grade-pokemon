#!/usr/bin/env python3
"""
Complete PSA grade prediction model training pipeline.
- Uses PyTorch with ResNet architecture
- Includes train/validation splits, data augmentation, early stopping
- Comprehensive evaluation metrics and model checkpointing
- Expects folder structure: dataset/<grade>/<images>
"""
import os
import json
import time
import numpy as np
import torch
import torchvision
from torchvision import transforms, datasets, models
from torch.utils.data import DataLoader, random_split, Subset
from torch import nn, optim
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
from datetime import datetime
import copy
from collections import defaultdict
import argparse


class FocalLoss(nn.Module):
    """Focuses learning on hard examples - reduces impact of easy samples"""
    def __init__(self, alpha=1, gamma=2, class_weights=None):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.class_weights = class_weights
        
    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, weight=self.class_weights, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1-pt)**self.gamma * ce_loss
        return focal_loss.mean()


class PSACustomLoss(nn.Module):
    """Custom loss function that heavily penalizes PSA 9/10 misclassification"""
    
    def __init__(self, class_weights, grade_9_10_penalty=10.0):
        super().__init__()
        self.class_weights = class_weights
        self.grade_9_10_penalty = grade_9_10_penalty
        self.base_criterion = nn.CrossEntropyLoss(weight=class_weights, reduction='none')
    
    def forward(self, outputs, targets):
        # Base weighted cross-entropy loss  
        base_loss = self.base_criterion(outputs, targets)
        
        # Additional penalty for 9/10 misclassification
        predicted_classes = outputs.argmax(dim=1)
        
        # Create penalty mask for 9/10 misclassification
        # Grade 9 = index 8, Grade 10 = index 9
        grade_9_mask = (targets == 8) & (predicted_classes == 9)  # True 9 predicted as 10
        grade_10_mask = (targets == 9) & (predicted_classes == 8)  # True 10 predicted as 9
        
        penalty_mask = grade_9_mask | grade_10_mask
        
        # Apply extra penalty to 9/10 misclassifications
        penalty_loss = base_loss * penalty_mask.float() * self.grade_9_10_penalty
        
        # Combine base loss with penalty
        total_loss = base_loss + penalty_loss
        
        return total_loss.mean()


class PSAGradeConfig:
    """Configuration class for training parameters"""
    def __init__(self, use_combined_images=False):
        self.DATA_DIR = 'dataset_combined' if use_combined_images else 'dataset'
        self.BATCH_SIZE = 32
        self.NUM_EPOCHS = 50
        self.NUM_CLASSES = 10  # PSA grades 1-10
        self.IMG_SIZE = 224
        self.IMG_WIDTH = 448 if use_combined_images else 224  # Wide for front+back
        self.LEARNING_RATE = 1e-4
        self.WEIGHT_DECAY = 1e-5
        self.PATIENCE = 7  # Early stopping patience
        self.TRAIN_SPLIT = 0.7
        self.VAL_SPLIT = 0.2
        self.TEST_SPLIT = 0.1
        self.MODEL_DIR = 'models'
        self.LOGS_DIR = 'logs'
        self.USE_COMBINED_IMAGES = use_combined_images
        
        # Enhanced training options
        self.USE_CURRICULUM_LEARNING = True
        self.USE_FOCAL_LOSS = True
        
        # Class weights - heavily weight PSA 9/10 distinction
        # Index 0 = Grade 1, Index 9 = Grade 10
        self.CLASS_WEIGHTS = torch.tensor([
            1.0,  # Grade 1
            1.0,  # Grade 2  
            1.0,  # Grade 3
            1.0,  # Grade 4
            1.0,  # Grade 5
            1.0,  # Grade 6
            1.0,  # Grade 7
            1.5,  # Grade 8 (slightly more important)
            3.0,  # Grade 9 (very important - high value cards)
            5.0   # Grade 10 (most important - premium cards)
        ])


class PSAGradeTrainer:
    def __init__(self, config):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")
        
        # Create directories
        os.makedirs(self.config.MODEL_DIR, exist_ok=True)
        os.makedirs(self.config.LOGS_DIR, exist_ok=True)
        
        # Training history
        self.train_losses = []
        self.val_losses = []
        self.train_accuracies = []
        self.val_accuracies = []
        
    def get_transforms(self):
        """Define data augmentation and preprocessing transforms"""
        if self.config.USE_COMBINED_IMAGES:
            # Handle wider combined front+back images (448x224)
            train_transform = transforms.Compose([
                transforms.Resize((self.config.IMG_SIZE + 32, self.config.IMG_WIDTH + 64)),
                transforms.RandomCrop((self.config.IMG_SIZE, self.config.IMG_WIDTH)),
                transforms.RandomHorizontalFlip(p=0.3),  # Less aggressive for card pairs
                transforms.RandomRotation(degrees=5),     # Reduced rotation for cards
                transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
                transforms.RandomAffine(degrees=0, translate=(0.05, 0.1)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            val_transform = transforms.Compose([
                transforms.Resize((self.config.IMG_SIZE, self.config.IMG_WIDTH)),
                transforms.ToTensor(), 
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        else:
            # Standard single-image transforms (224x224)
            train_transform = transforms.Compose([
                transforms.Resize((self.config.IMG_SIZE + 32, self.config.IMG_SIZE + 32)),
                transforms.RandomCrop((self.config.IMG_SIZE, self.config.IMG_SIZE)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(degrees=10),
                transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
                transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            val_transform = transforms.Compose([
                transforms.Resize((self.config.IMG_SIZE, self.config.IMG_SIZE)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        
        return train_transform, val_transform
    
    def prepare_data(self):
        """Create train/validation/test data loaders"""
        # Check if dataset directory exists
        if not os.path.exists(self.config.DATA_DIR):
            print(f"❌ Dataset directory '{self.config.DATA_DIR}' not found!")
            print("Please prepare your dataset first by running:")
            print("  python prepare_dataset.py")
            print("\nThis will download and organize images from your JSON data.")
            raise FileNotFoundError(f"Dataset directory '{self.config.DATA_DIR}' does not exist")
            
        train_transform, val_transform = self.get_transforms()
        
        # Load full dataset
        try:
            full_dataset = datasets.ImageFolder(self.config.DATA_DIR, transform=val_transform)
        except Exception as e:
            print(f"❌ Error loading dataset from '{self.config.DATA_DIR}': {e}")
            print("\nMake sure your dataset has the correct structure:")
            print("dataset/")
            print("  1/")
            print("    image1.jpg")
            print("    image2.jpg")
            print("  2/")
            print("    image1.jpg")
            print("  ...")
            print("  10/")
            print("    image1.jpg")
            raise
        
        # Calculate split sizes
        total_size = len(full_dataset)
        train_size = int(self.config.TRAIN_SPLIT * total_size)
        val_size = int(self.config.VAL_SPLIT * total_size)
        test_size = total_size - train_size - val_size
        
        print(f"Dataset splits: Train={train_size}, Val={val_size}, Test={test_size}")
        
        # Split dataset
        train_dataset, val_dataset, test_dataset = random_split(
            full_dataset, [train_size, val_size, test_size],
            generator=torch.Generator().manual_seed(42)
        )
        
        # Apply training transforms to train set
        train_dataset.dataset.transform = train_transform
        
        # Create data loaders
        self.train_loader = DataLoader(
            train_dataset, batch_size=self.config.BATCH_SIZE, 
            shuffle=True, num_workers=4, pin_memory=True
        )
        self.val_loader = DataLoader(
            val_dataset, batch_size=self.config.BATCH_SIZE,
            shuffle=False, num_workers=4, pin_memory=True
        )
        self.test_loader = DataLoader(
            test_dataset, batch_size=self.config.BATCH_SIZE,
            shuffle=False, num_workers=4, pin_memory=True
        )
        
        # Store class names
        self.class_names = full_dataset.classes
        print(f"Classes found: {self.class_names}")
        
    def create_model(self):
        """Initialize the model architecture"""
        model = models.resnet50(weights='IMAGENET1K_V1')  # Updated for newer PyTorch
        
        # Freeze early layers
        for param in list(model.parameters())[:-20]:
            param.requires_grad = False
            
        # Replace final layer
        num_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, self.config.NUM_CLASSES)
        )
        
        return model.to(self.device)
    
    def train_epoch(self, model, optimizer, criterion):
        """Train for one epoch"""
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for batch_idx, (images, labels) in enumerate(self.train_loader):
            images, labels = images.to(self.device), labels.to(self.device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            
            if batch_idx % 10 == 0:
                print(f'Batch {batch_idx}/{len(self.train_loader)}, Loss: {loss.item():.4f}')
        
        epoch_loss = running_loss / len(self.train_loader)
        epoch_acc = 100. * correct / total
        
        return epoch_loss, epoch_acc
    
    def validate(self, model, criterion):
        """Validate the model"""
        model.eval()
        running_loss = 0.0
        correct = 0
        total = 0
        all_predictions = []
        all_labels = []
        
        with torch.no_grad():
            for images, labels in self.val_loader:
                images, labels = images.to(self.device), labels.to(self.device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                
                running_loss += loss.item()
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()
                
                # Collect predictions for detailed analysis
                all_predictions.extend(predicted.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        epoch_loss = running_loss / len(self.val_loader)
        epoch_acc = 100. * correct / total
        
        return epoch_loss, epoch_acc, all_predictions, all_labels
    
    def train_model(self, model=None, model_name="psa_grade_model"):
        """Enhanced training with early stopping"""
        if model is None:
            model = self.create_model()
        
        # Setup loss function
        if self.config.USE_FOCAL_LOSS:
            criterion = FocalLoss(alpha=1, gamma=2, class_weights=self.config.CLASS_WEIGHTS.to(self.device))
        else:
            criterion = PSACustomLoss(self.config.CLASS_WEIGHTS.to(self.device))
        
        optimizer = optim.AdamW(model.parameters(), lr=self.config.LEARNING_RATE, weight_decay=self.config.WEIGHT_DECAY)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)
        
        best_model_state = None
        best_val_acc = 0.0
        patience_counter = 0
        
        print(f"🚀 Starting training for {model_name}...")
        print(f"📊 Loss function: {'Focal Loss' if self.config.USE_FOCAL_LOSS else 'Custom PSA Loss'}")
        
        for epoch in range(self.config.NUM_EPOCHS):
            start_time = time.time()
            
            # Training
            train_loss, train_acc = self.train_epoch(model, optimizer, criterion)
            
            # Validation
            val_loss, val_acc, val_predictions, val_labels = self.validate(model, criterion)
            
            # Learning rate scheduling
            scheduler.step(val_loss)
            
            # Track training history
            self.train_losses.append(train_loss)
            self.val_losses.append(val_loss)
            self.train_accuracies.append(train_acc)
            self.val_accuracies.append(val_acc)
            
            epoch_time = time.time() - start_time
            
            print(f"Epoch {epoch+1:3d}/{self.config.NUM_EPOCHS} | "
                  f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
                  f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}% | "
                  f"Time: {epoch_time:.1f}s")
            
            # Save best model
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_model_state = copy.deepcopy(model.state_dict())
                patience_counter = 0
                print(f"💾 New best model! Val accuracy: {val_acc:.2f}%")
            else:
                patience_counter += 1
                
            # Early stopping
            if patience_counter >= self.config.PATIENCE:
                print(f"⏰ Early stopping triggered after {epoch+1} epochs")
                break
        
        # Load best model
        if best_model_state is not None:
            model.load_state_dict(best_model_state)
            print(f"✅ Loaded best model with validation accuracy: {best_val_acc:.2f}%")
        
        # Save model
        model_path = os.path.join(self.config.MODEL_DIR, f'{model_name}_best.pth')
        torch.save({
            'epoch': epoch + 1,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'best_val_acc': best_val_acc,
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'config': self.config
        }, model_path)
        
        print(f"✅ Model saved: {model_path}")
        return model_path


def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description="PSA Grade Prediction Training")
    parser.add_argument('--combined', action='store_true', 
                       help='Use combined front+back images for training (more accurate)')
    args = parser.parse_args()
    
    print("🎯 PSA Grade Prediction Training")
    print("=" * 50)
    
    # Configuration
    use_combined_images = args.combined
    config = PSAGradeConfig(use_combined_images=use_combined_images)
    
    print(f"📂 Data directory: {config.DATA_DIR}")
    print(f"🖼️  Image size: {config.IMG_SIZE}x{config.IMG_WIDTH}")
    print(f"🎯 Focal loss: {config.USE_FOCAL_LOSS}")
    
    if use_combined_images:
        print("✨ Using combined front+back images for complete card assessment")
    else:
        print("📷 Using front images only")
    
    # Initialize trainer
    trainer = PSAGradeTrainer(config)
    
    # Prepare data
    print("\n📊 Preparing dataset...")
    trainer.prepare_data()
    
    # Training
    try:
        print("\n🚀 Starting model training...")
        model_path = trainer.train_model()
        print(f"✅ Training complete! Model saved: {model_path}")
                
    except KeyboardInterrupt:
        print("\n⏹️  Training interrupted by user")
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        raise


if __name__ == "__main__":
    main()