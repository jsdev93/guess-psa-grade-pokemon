#!/usr/bin/env python3
"""
PSA 9/10 Specific Accuracy Checker
Shows performance on gem mint grades that matter for investment
"""
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
import numpy as np
from dual_input_trainer import PSADualTrainer, PSADualInputModel

def check_psa_910_accuracy(model_path='models/psa_dual_concat_best.pth'):
    """Check PSA 9/10 specific performance"""
    
    print("🔍 PSA 9/10 Specific Accuracy Analysis")
    print("=" * 50)
    
    # Create trainer and load data
    trainer = PSADualTrainer('dataset', fusion_method='concat')
    trainer.prepare_data(batch_size=32)
    
    # Load model
    model = PSADualInputModel(num_classes=10, fusion_method='concat', input_size=(80, 128))
    checkpoint = torch.load(model_path, map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    print(f"✅ Model loaded: {model_path}")
    
    # Run evaluation on validation set
    all_preds = []
    all_targets = []
    all_probs = []
    
    with torch.no_grad():
        for front_imgs, back_imgs, labels in trainer.val_loader:
            outputs = model(front_imgs, back_imgs)
            probabilities = F.softmax(outputs, dim=1)
            predicted = outputs.argmax(dim=1)
            
            all_preds.extend(predicted.cpu().numpy())
            all_targets.extend(labels.cpu().numpy())
            all_probs.extend(probabilities.cpu().numpy())
    
    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)
    all_probs = np.array(all_probs)
    
    # Overall accuracy
    overall_acc = (all_preds == all_targets).mean()
    print(f"📊 Overall Validation Accuracy: {overall_acc:.2%}")
    
    # PSA 9/10 SPECIFIC METRICS
    print(f"\n💎 PSA 9/10 SPECIFIC PERFORMANCE:")
    
    # 1. PSA 9/10 Detection Accuracy
    psa_9_mask = all_targets == 8  # PSA 9 (0-indexed)
    psa_10_mask = all_targets == 9  # PSA 10 (0-indexed)
    gem_mint_mask = psa_9_mask | psa_10_mask
    
    if gem_mint_mask.sum() > 0:
        # How well does it detect gem mint cards?
        gem_mint_detected = ((all_preds[gem_mint_mask] == 8) | (all_preds[gem_mint_mask] == 9))
        gem_mint_detection_acc = gem_mint_detected.sum() / gem_mint_mask.sum()
        
        print(f"🎯 Gem Mint Detection (9 or 10): {gem_mint_detection_acc:.2%}")
        
        # Individual grade accuracy
        if psa_9_mask.sum() > 0:
            psa_9_correct = (all_preds[psa_9_mask] == 8).sum()
            psa_9_acc = psa_9_correct / psa_9_mask.sum()
            print(f"9️⃣  PSA 9 Accuracy: {psa_9_acc:.2%} ({psa_9_correct}/{psa_9_mask.sum()})")
        
        if psa_10_mask.sum() > 0:
            psa_10_correct = (all_preds[psa_10_mask] == 9).sum()
            psa_10_acc = psa_10_correct / psa_10_mask.sum()
            print(f"🔟 PSA 10 Accuracy: {psa_10_acc:.2%} ({psa_10_correct}/{psa_10_mask.sum()})")
        
        # 2. PSA 9/10 CONFUSION ANALYSIS
        print(f"\n⚠️  PSA 9/10 CONFUSION:")
        psa_9_as_10 = ((all_targets == 8) & (all_preds == 9)).sum()
        psa_10_as_9 = ((all_targets == 9) & (all_preds == 8)).sum()
        
        print(f"   PSA 9 predicted as 10: {psa_9_as_10} cards")
        print(f"   PSA 10 predicted as 9: {psa_10_as_9} cards")
        
        confusion_rate = (psa_9_as_10 + psa_10_as_9) / gem_mint_mask.sum()
        print(f"   9↔10 Confusion Rate: {confusion_rate:.2%}")
        
        # 3. INVESTMENT METRICS
        print(f"\n💰 INVESTMENT DECISION METRICS:")
        
        # Precision: When model says "PSA 10", how often is it right?
        predicted_10_mask = all_preds == 9
        if predicted_10_mask.sum() > 0:
            psa_10_precision = ((all_targets == 9) & (all_preds == 9)).sum() / predicted_10_mask.sum()
            print(f"   PSA 10 Precision: {psa_10_precision:.2%} (When model says '10', it's right)")
        
        # Recall: Of all PSA 10s, how many does model find?
        if psa_10_mask.sum() > 0:
            psa_10_recall = ((all_targets == 9) & (all_preds == 9)).sum() / psa_10_mask.sum()
            print(f"   PSA 10 Recall: {psa_10_recall:.2%} (Model finds this % of all PSA 10s)")
        
        # Conservative investment strategy
        high_confidence_10s = (all_probs[:, 9] > 0.6) & (all_preds == 9)
        if high_confidence_10s.sum() > 0:
            high_conf_precision = ((all_targets == 9) & high_confidence_10s).sum() / high_confidence_10s.sum()
            print(f"   High-Confidence PSA 10s (>60%): {high_conf_precision:.2%} precision")
        
        print(f"\n🎯 SUMMARY FOR INVESTMENT:")
        if gem_mint_detection_acc > 0.7:
            print("✅ Strong gem mint detection - Good for investment screening")
        else:
            print("⚠️  Moderate gem mint detection - Use with caution")
            
        if confusion_rate < 0.15:
            print("✅ Low 9/10 confusion - Reliable for grade distinction")
        else:
            print("⚠️  Higher 9/10 confusion - Consider ensemble methods")

if __name__ == "__main__":
    import sys
    model_path = sys.argv[1] if len(sys.argv) > 1 else 'models/psa_dual_concat_best.pth'
    check_psa_910_accuracy(model_path)