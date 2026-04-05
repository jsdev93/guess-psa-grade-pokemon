#!/usr/bin/env python3
"""
Dual-input PSA Grade Prediction Model
Processes front and back images separately, then fuses features for better accuracy.
"""
import os
import json
import time
import numpy as np
import torch
import torchvision
from torchvision import transforms, datasets, models
from torch.utils.data import DataLoader, Dataset, random_split
from torch import nn, optim
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, confusion_matrix
from PIL import Image
from datetime import datetime
import copy
from pathlib import Path
import argparse


class PSADualImageDataset(Dataset):
    """Dataset that loads both front and back images for each card"""
    
    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.samples = []
        
        # Collect all front/back pairs
        for grade_folder in sorted(self.data_dir.iterdir()):
            if not grade_folder.is_dir():
                continue
                
            grade = int(grade_folder.name) - 1  # Convert to 0-indexed
            
            # Group images by item ID
            image_pairs = {}
            for img_file in grade_folder.glob('*.jpg'):
                parts = img_file.stem.split('_')
                if len(parts) >= 2:
                    item_id = '_'.join(parts[:-1])
                    side = parts[-1]
                    
                    if item_id not in image_pairs:
                        image_pairs[item_id] = {}
                    image_pairs[item_id][side] = img_file
            
            # Add valid pairs to samples
            for item_id, sides in image_pairs.items():
                if 'front' in sides and 'back' in sides:
                    self.samples.append({
                        'front_path': sides['front'],
                        'back_path': sides['back'],
                        'grade': grade,
                        'item_id': item_id
                    })
        
        print(f"Found {len(self.samples)} front+back pairs")
        
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        
        # Load front and back images
        front_img = Image.open(sample['front_path']).convert('RGB')
        back_img = Image.open(sample['back_path']).convert('RGB')
        
        # Apply transforms
        if self.transform:
            front_img = self.transform(front_img)
            back_img = self.transform(back_img)
        
        return front_img, back_img, sample['grade']


class PSADualInputModel(nn.Module):
    """Dual-input model that processes front and back images separately with natural aspect ratios"""
    
    def __init__(self, num_classes=10, fusion_method='concat', input_size=(400, 640)):
        super().__init__()
        self.fusion_method = fusion_method
        self.input_size = input_size
        
        # Use a much lighter backbone for CPU training
        backbone = models.resnet18(weights='IMAGENET1K_V1')  # Much lighter than ResNet50
        
        # Remove final avgpool and fc layers
        self.features = nn.Sequential(*list(backbone.children())[:-2])
        
        # Freeze early layers for transfer learning
        for param in list(self.features.parameters())[:-20]:
            param.requires_grad = False
        
        # Adaptive pooling to handle variable input sizes
        self.adaptive_pool = nn.AdaptiveAvgPool2d((7, 7))  # Output 7x7 feature maps
        
        # Calculate feature dimension after adaptive pooling
        # ResNet18 outputs 512 channels, with 7x7 spatial = 512 * 49 = 25,088
        feature_dim = 512 * 7 * 7  # Much smaller feature space
        
        # Lighter feature compression
        self.feature_compress = nn.Sequential(
            nn.Linear(feature_dim, 256),  # Much smaller compression
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        compressed_dim = 256
        
        # Fusion layer
        if fusion_method == 'concat':
            # Concatenate front and back features
            fused_dim = compressed_dim * 2
        elif fusion_method == 'add':
            # Element-wise addition
            fused_dim = compressed_dim
        elif fusion_method == 'attention':
            # Attention-based fusion
            self.attention = nn.MultiheadAttention(compressed_dim, num_heads=8, batch_first=True)
            fused_dim = compressed_dim
        
        # Lighter classification head
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(fused_dim, 128),  # Smaller intermediate layer
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes)
        )
        
        print(f"🏗️  Lightweight model configured for {input_size} input size")
        print(f"🔗 Feature dimension: {feature_dim} → {compressed_dim} (compressed)")
        print(f"🔀 Fusion method: {fusion_method}, Final dim: {fused_dim}")
    
    def forward(self, front_img, back_img):
        batch_size = front_img.size(0)
        
        # Extract features from both images
        front_features = self.features(front_img)  # [batch, 2048, H, W]
        back_features = self.features(back_img)    # [batch, 2048, H, W]
        
        # Apply adaptive pooling to standardize spatial dimensions
        front_features = self.adaptive_pool(front_features)  # [batch, 2048, 7, 7]
        back_features = self.adaptive_pool(back_features)    # [batch, 2048, 7, 7]
        
        # Flatten features
        front_features = front_features.view(batch_size, -1)  # [batch, 2048*7*7]
        back_features = back_features.view(batch_size, -1)    # [batch, 2048*7*7]
        
        # Compress features
        front_features = self.feature_compress(front_features)  # [batch, 2048]
        back_features = self.feature_compress(back_features)    # [batch, 2048]
        
        # Fuse features
        if self.fusion_method == 'concat':
            # Concatenate features
            fused_features = torch.cat([front_features, back_features], dim=1)
        elif self.fusion_method == 'add':
            # Element-wise addition
            fused_features = front_features + back_features
        elif self.fusion_method == 'attention':
            # Attention-based fusion
            stacked = torch.stack([front_features, back_features], dim=1)  # [batch, 2, 2048]
            attended, _ = self.attention(stacked, stacked, stacked)
            fused_features = attended.mean(dim=1)  # Average attended features
        
        # Classification
        output = self.classifier(fused_features)
        return output


class PSADualTrainer:
    """Trainer for dual-input PSA grade prediction"""
    
    def __init__(self, data_dir, fusion_method='concat', device=None):
        self.data_dir = data_dir
        self.fusion_method = fusion_method
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        print(f"🎯 PSA Dual-Input Model with {fusion_method} fusion")
        print(f"📱 Using device: {self.device}")
        
        # Create directories
        os.makedirs('models', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
    def get_transforms(self):
        """Get transforms that preserve original aspect ratios"""
        # Calculate target size that preserves aspect ratio - ultra-lightweight for CPU
        target_height = 128  # Much smaller for fast CPU training
        target_width = 80    # Maintains ~0.6 aspect ratio like original images
        
        train_transform = transforms.Compose([
            # Resize maintaining aspect ratio, then center crop to exact size
            transforms.Resize((target_height + 32, target_width + 32)),  # Slightly larger for random crop
            transforms.RandomCrop((target_height, target_width)),
            transforms.RandomHorizontalFlip(p=0.3),  # Less aggressive for cards
            transforms.RandomRotation(degrees=5),     # Small rotation for cards
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        val_transform = transforms.Compose([
            transforms.Resize((target_height, target_width)),  # Direct resize for validation
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        print(f"🖼️  Using natural aspect ratio: {target_width}x{target_height} (preserves card proportions)")
        return train_transform, val_transform
    
    def prepare_data(self, batch_size=32, train_split=0.7, val_split=0.2):
        """Prepare dual-input data loaders"""
        train_transform, val_transform = self.get_transforms()
        
        # Create full dataset
        full_dataset = PSADualImageDataset(self.data_dir, transform=val_transform)
        
        if len(full_dataset) == 0:
            raise ValueError(f"No front+back image pairs found in {self.data_dir}")
        
        # Split dataset
        total_size = len(full_dataset)
        train_size = int(train_split * total_size)
        val_size = int(val_split * total_size)
        test_size = total_size - train_size - val_size
        
        train_dataset, val_dataset, test_dataset = random_split(
            full_dataset, [train_size, val_size, test_size],
            generator=torch.Generator().manual_seed(42)
        )
        
        print(f"📊 Dataset splits: Train={train_size}, Val={val_size}, Test={test_size}")
        
        # Apply training transforms to train set
        train_dataset.dataset.transform = train_transform
        
        # Create data loaders - optimized for CPU training
        self.train_loader = DataLoader(
            train_dataset, batch_size=batch_size, shuffle=True, 
            num_workers=2, pin_memory=False
        )
        self.val_loader = DataLoader(
            val_dataset, batch_size=batch_size, shuffle=False,
            num_workers=2, pin_memory=False
        )
        self.test_loader = DataLoader(
            test_dataset, batch_size=batch_size, shuffle=False,
            num_workers=2, pin_memory=False
        )
    
    def train_model(self, num_epochs=50, lr=1e-4, patience=7):
        """Train the dual-input model"""
        model = PSADualInputModel(num_classes=10, fusion_method=self.fusion_method, input_size=(80, 128))
        model = model.to(self.device)
        
        # Loss and optimizer with class weights for PSA 9/10 focus
        class_weights = torch.tensor([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.5, 3.0, 5.0]).to(self.device)
        criterion = nn.CrossEntropyLoss(weight=class_weights)
        optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-5)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)
        
        best_val_acc = 0.0
        patience_counter = 0
        best_model_state = None
        
        print(f"🚀 Training dual-input model for {num_epochs} epochs...")
        
        for epoch in range(num_epochs):
            start_time = time.time()
            
            # Training phase
            model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0
            
            for batch_idx, (front_imgs, back_imgs, labels) in enumerate(self.train_loader):
                front_imgs = front_imgs.to(self.device)
                back_imgs = back_imgs.to(self.device)
                labels = labels.to(self.device)
                
                optimizer.zero_grad()
                outputs = model(front_imgs, back_imgs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
                _, predicted = outputs.max(1)
                train_total += labels.size(0)
                train_correct += predicted.eq(labels).sum().item()
                
                if batch_idx % 10 == 0:
                    print(f'Batch {batch_idx}/{len(self.train_loader)}, Loss: {loss.item():.4f}')
            
            # Validation phase
            model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for front_imgs, back_imgs, labels in self.val_loader:
                    front_imgs = front_imgs.to(self.device)
                    back_imgs = back_imgs.to(self.device)
                    labels = labels.to(self.device)
                    
                    outputs = model(front_imgs, back_imgs)
                    loss = criterion(outputs, labels)
                    
                    val_loss += loss.item()
                    _, predicted = outputs.max(1)
                    val_total += labels.size(0)
                    val_correct += predicted.eq(labels).sum().item()
            
            # Calculate metrics
            train_acc = 100. * train_correct / train_total
            val_acc = 100. * val_correct / val_total
            epoch_time = time.time() - start_time
            
            print(f"Epoch {epoch+1:3d}/{num_epochs} | "
                  f"Train Loss: {train_loss/len(self.train_loader):.4f} | Train Acc: {train_acc:.2f}% | "
                  f"Val Loss: {val_loss/len(self.val_loader):.4f} | Val Acc: {val_acc:.2f}% | "
                  f"Time: {epoch_time:.1f}s")
            
            # Learning rate scheduling
            scheduler.step(val_loss)
            
            # Save best model
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_model_state = copy.deepcopy(model.state_dict())
                patience_counter = 0
                print(f"💾 New best model! Val accuracy: {val_acc:.2f}%")
            else:
                patience_counter += 1
            
            # Early stopping
            if patience_counter >= patience:
                print(f"⏰ Early stopping after {epoch+1} epochs")
                break
        
        # Load best model
        if best_model_state is not None:
            model.load_state_dict(best_model_state)
            print(f"✅ Loaded best model with validation accuracy: {best_val_acc:.2f}%")
        
        # Save model
        model_path = f'models/psa_dual_{self.fusion_method}_best.pth'
        torch.save({
            'model_state_dict': model.state_dict(),
            'best_val_acc': best_val_acc,
            'fusion_method': self.fusion_method,
            'epoch': epoch + 1
        }, model_path)
        
        print(f"✅ Model saved: {model_path}")
        return model_path


def main():
    parser = argparse.ArgumentParser(description="Dual-Input PSA Grade Prediction")
    parser.add_argument('--data-dir', default='dataset', help='Dataset directory with front/back images')
    parser.add_argument('--fusion', choices=['concat', 'add', 'attention'], default='concat',
                       help='Feature fusion method')
    parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--lr', type=float, default=1e-4, help='Learning rate')
    
    args = parser.parse_args()
    
    print("🎯 PSA Dual-Input Model Training")
    print("=" * 50)
    print(f"📁 Data directory: {args.data_dir}")
    print(f"🔗 Fusion method: {args.fusion}")
    print(f"🔄 Epochs: {args.epochs}")
    
    try:
        trainer = PSADualTrainer(args.data_dir, fusion_method=args.fusion)
        trainer.prepare_data(batch_size=args.batch_size)
        model_path = trainer.train_model(num_epochs=args.epochs, lr=args.lr)
        
        print(f"\n🎉 Training completed successfully!")
        print(f"📁 Model saved: {model_path}")
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        raise


if __name__ == "__main__":
    main()