#!/usr/bin/env python3
"""
PSA 9/10 Performance Checker
Analyzes PSA grade prediction performance for original dual-input models
"""
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
import numpy as np
import os

def check_any_model_psa_performance(model_path):
    """Check PSA 9/10 performance for dual-input model"""
    
    print("🔍 PSA 9/10 Analysis")
    print("=" * 50)
    print(f"📁 Model: {model_path}")
    
    # Load checkpoint
    checkpoint = torch.load(model_path, map_location='cpu')
    print(f"📊 Model saved at epoch: {checkpoint.get('epoch', 'unknown')}")
    
    print("⚡ Loading dual-input model")
    print(f"🔗 Fusion method: {checkpoint.get('fusion_method', 'concat')}")
    
    # Import original model
    from dual_input_trainer import PSADualInputModel, PSADualTrainer
    model = PSADualInputModel(
        num_classes=10,
        fusion_method=checkpoint.get('fusion_method', 'concat'),
        input_size=(80, 128)
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    
    # Original model setup
    input_size = (80, 128)
    trainer = PSADualTrainer('dataset', fusion_method=checkpoint.get('fusion_method', 'concat'))
    
    # Prepare data
    trainer.prepare_data(batch_size=32)
    model.eval()
    
    print(f"✅ Model loaded successfully!")
    print(f"🖼️  Input size: {input_size}")
    
    # Run evaluation
    print(f"\\n📊 Running PSA 9/10 evaluation...")
    
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
    
    # Calculate metrics
    overall_acc = (all_preds == all_targets).mean()
    best_val_acc = checkpoint.get('best_val_acc', overall_acc * 100)
    
    print(f"\\n📈 ACCURACY RESULTS:")
    print(f"🎯 Overall Validation Accuracy: {overall_acc:.2%}")
    print(f"🏆 Best Training Accuracy: {best_val_acc:.2f}%")
    
    # PSA 9/10 analysis
    psa_9_mask = all_targets == 8  # PSA 9 (0-indexed)
    psa_10_mask = all_targets == 9  # PSA 10 (0-indexed)
    gem_mint_mask = psa_9_mask | psa_10_mask
    
    if gem_mint_mask.sum() > 0:
        print(f"\\n💎 PSA 9/10 SPECIFIC PERFORMANCE:")
        
        # Gem mint detection
        gem_mint_detected = ((all_preds[gem_mint_mask] == 8) | (all_preds[gem_mint_mask] == 9))
        gem_mint_detection_acc = gem_mint_detected.sum() / gem_mint_mask.sum()
        print(f"🎯 Gem Mint Detection (9 or 10): {gem_mint_detection_acc:.2%}")
        
        # Individual accuracies
        if psa_9_mask.sum() > 0:
            psa_9_correct = (all_preds[psa_9_mask] == 8).sum()
            psa_9_acc = psa_9_correct / psa_9_mask.sum()
            print(f"9️⃣  PSA 9 Accuracy: {psa_9_acc:.2%} ({psa_9_correct}/{psa_9_mask.sum()})")
        
        if psa_10_mask.sum() > 0:
            psa_10_correct = (all_preds[psa_10_mask] == 9).sum()
            psa_10_acc = psa_10_correct / psa_10_mask.sum()
            print(f"🔟 PSA 10 Accuracy: {psa_10_acc:.2%} ({psa_10_correct}/{psa_10_mask.sum()})")
        
        # Confusion analysis
        psa_9_as_10 = ((all_targets == 8) & (all_preds == 9)).sum()
        psa_10_as_9 = ((all_targets == 9) & (all_preds == 8)).sum()
        confusion_rate = (psa_9_as_10 + psa_10_as_9) / gem_mint_mask.sum()
        
        print(f"\\n⚠️  PSA 9/10 CONFUSION:")
        print(f"   PSA 9 → 10 errors: {psa_9_as_10}")
        print(f"   PSA 10 → 9 errors: {psa_10_as_9}")
        print(f"   9↔10 Confusion Rate: {confusion_rate:.2%}")
        
        # Investment metrics
        print(f"\\n💰 INVESTMENT METRICS:")
        
        # PSA 10 precision/recall
        predicted_10_mask = all_preds == 9
        if predicted_10_mask.sum() > 0:
            psa_10_precision = ((all_targets == 9) & (all_preds == 9)).sum() / predicted_10_mask.sum()
            print(f"   PSA 10 Precision: {psa_10_precision:.2%} (When model says '10', it's right)")
        
        if psa_10_mask.sum() > 0:
            psa_10_recall = ((all_targets == 9) & (all_preds == 9)).sum() / psa_10_mask.sum()
            print(f"   PSA 10 Recall: {psa_10_recall:.2%} (Finds {psa_10_recall:.1%} of all PSA 10s)")
        
        # High confidence predictions
        high_confidence_10s = (all_probs[:, 9] > 0.6) & (all_preds == 9)
        if high_confidence_10s.sum() > 0:
            high_conf_precision = ((all_targets == 9) & high_confidence_10s).sum() / high_confidence_10s.sum()
            print(f"   High-Confidence PSA 10s (>60%): {high_conf_precision:.2%} precision")
        
        # Ultra conservative (70%+ confidence)
        ultra_confidence_10s = (all_probs[:, 9] > 0.7) & (all_preds == 9)
        if ultra_confidence_10s.sum() > 0:
            ultra_conf_precision = ((all_targets == 9) & ultra_confidence_10s).sum() / ultra_confidence_10s.sum()
            print(f"   Ultra-Conservative PSA 10s (>70%): {ultra_conf_precision:.2%} precision")
        
        # SUMMARY
        print(f"\\n🎯 INVESTMENT SUMMARY:")
        improvement_vs_baseline = overall_acc * 100 - 59.47
        if improvement_vs_baseline > 0:
            print(f"✅ Improved by {improvement_vs_baseline:.1f}% over baseline (59.47%)")
        
        if gem_mint_detection_acc > 0.95:
            print("✅ Excellent gem mint detection")
        elif gem_mint_detection_acc > 0.85:
            print("✅ Good gem mint detection")
        else:
            print("⚠️  Moderate gem mint detection")
        
        if confusion_rate < 0.15:
            print("✅ Low PSA 9/10 confusion - reliable for investments")
        elif confusion_rate < 0.25:
            print("🔶 Moderate PSA 9/10 confusion - use with caution")
        else:
            print("⚠️  High PSA 9/10 confusion - consider ensemble methods")
        
    return {
        'overall_accuracy': overall_acc,
        'best_training_accuracy': best_val_acc,
        'gem_mint_detection': gem_mint_detection_acc if gem_mint_mask.sum() > 0 else 0,
        'psa_10_precision': psa_10_precision if predicted_10_mask.sum() > 0 else 0,
        'psa_10_recall': psa_10_recall if psa_10_mask.sum() > 0 else 0,
        'confusion_rate': confusion_rate if gem_mint_mask.sum() > 0 else 0
    }


def compare_models():
    """Compare all available models"""
    print("🏆 MODEL COMPARISON")
    print("=" * 60)
    
    models_to_check = []
    if os.path.exists('models/psa_dual_concat_best.pth'):
        models_to_check.append(('Original Model', 'models/psa_dual_concat_best.pth'))
    
    if not models_to_check:
        print("❌ No models found to compare")
        return
    
    results = {}
    for name, path in models_to_check:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            results[name] = check_any_model_psa_performance(path)
        except Exception as e:
            print(f"❌ Error checking {name}: {e}")
    
    # Summary comparison
    if len(results) > 1:
        print(f"\n🏆 FINAL COMPARISON:")
        print("-" * 60)
        for name, metrics in results.items():
            print(f"{name:25} | Overall: {metrics['overall_accuracy']:.1%} | PSA 10 Precision: {metrics['psa_10_precision']:.1%}")
    else:
        print(f"\n✅ Analysis complete for {list(results.keys())[0]}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
        check_any_model_psa_performance(model_path)
    else:
        compare_models()