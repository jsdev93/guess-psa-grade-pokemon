#!/usr/bin/env python3
"""
Explainable PSA Grade Predictor
Shows WHY a card gets a specific grade and what prevents it from being higher
"""
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import cv2
from dual_input_trainer import PSADualTrainer, PSADualInputModel
import os

class ExplainablePSAPredictor:
    """Predicts PSA grades with detailed explanations"""
    
    def __init__(self, model_path='models/psa_dual_concat_best.pth'):
        self.model_path = model_path
        self.trainer = PSADualTrainer('dataset', fusion_method='concat')
        self.device = torch.device('cpu')
        
        # Load model
        self.model = PSADualInputModel(num_classes=10, fusion_method='concat', input_size=(80, 128))
        checkpoint = torch.load(model_path, map_location='cpu')
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        # Get transforms
        _, self.transform, _ = self.trainer.get_transforms()
        
        print("🔍 Explainable PSA Predictor loaded!")
    
    def predict_with_explanation(self, front_img_path, back_img_path):
        """Predict grade with detailed explanation"""
        
        print(f"\\n🔮 EXPLAINABLE PSA PREDICTION")
        print("=" * 50)
        
        # Load and preprocess images
        front_img = Image.open(front_img_path).convert('RGB')
        back_img = Image.open(back_img_path).convert('RGB')
        
        front_tensor = self.transform(front_img).unsqueeze(0)
        back_tensor = self.transform(back_img).unsqueeze(0)
        
        # Make prediction with gradients enabled for explanation
        front_tensor.requires_grad_(True)
        back_tensor.requires_grad_(True)
        
        outputs = self.model(front_tensor, back_tensor)
        probabilities = F.softmax(outputs, dim=1)
        predicted_grade = outputs.argmax(dim=1).item() + 1
        confidence = probabilities.max().item()
        
        # Detailed grade analysis
        grade_probs = probabilities[0].detach().numpy()
        
        print(f"🎯 PREDICTION RESULT:")
        print(f"   Predicted Grade: PSA {predicted_grade}")
        print(f"   Confidence: {confidence:.2%}")
        
        # Show top 3 most likely grades
        top_3_indices = np.argsort(grade_probs)[-3:][::-1]
        print(f"\\n📊 TOP 3 PREDICTIONS:")
        for i, idx in enumerate(top_3_indices):
            grade = idx + 1
            prob = grade_probs[idx]
            icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉"
            print(f"   {icon} PSA {grade}: {prob:.2%}")
        
        # Explain why not higher grade
        print(f"\\n🤔 WHY NOT PSA 10?")
        psa_10_prob = grade_probs[9]  # PSA 10 is index 9
        psa_9_prob = grade_probs[8]   # PSA 9 is index 8
        
        if predicted_grade < 10:
            deficit = grade_probs[9] - grade_probs[predicted_grade-1]
            print(f"   PSA 10 Probability: {psa_10_prob:.2%}")
            print(f"   Predicted Grade Prob: {grade_probs[predicted_grade-1]:.2%}")
            print(f"   Deficit to PSA 10: {-deficit:.2%}")
            
            # Analyze what's holding it back
            if psa_10_prob < 0.3:
                print(f"   🔴 LOW PSA 10 confidence - model sees significant issues")
            elif psa_10_prob < 0.5:
                print(f"   🟡 MODERATE PSA 10 confidence - some minor issues detected")
            else:
                print(f"   🟢 HIGH PSA 10 confidence - very close to perfect!")
        
        # Feature importance analysis
        print(f"\\n🔬 FEATURE ANALYSIS:")
        self._analyze_image_features(front_img, back_img, front_tensor, back_tensor, outputs)
        
        # Generate attention heatmaps
        print(f"\\n🗺️  ATTENTION ANALYSIS:")
        self._generate_attention_maps(front_img, back_img, front_tensor, back_tensor, outputs, predicted_grade)
        
        # Comparison with perfect grade
        print(f"\\n💎 WHAT WOULD MAKE IT PSA 10?")
        self._suggest_improvements(grade_probs, predicted_grade)
        
        return {
            'predicted_grade': predicted_grade,
            'confidence': confidence,
            'grade_probabilities': {f'PSA {i+1}': prob for i, prob in enumerate(grade_probs)},
            'psa_10_deficit': grade_probs[9] - grade_probs[predicted_grade-1] if predicted_grade < 10 else 0,
            'explanation': self._generate_explanation(grade_probs, predicted_grade)
        }
    
    def _analyze_image_features(self, front_img, back_img, front_tensor, back_tensor, outputs):
        """Analyze which parts of images contribute to prediction"""
        
        # Get gradients to see what the model focuses on
        predicted_class = outputs.argmax(dim=1).item()
        class_score = outputs[0, predicted_class]
        
        # Compute gradients
        class_score.backward(retain_graph=True)
        
        front_grads = front_tensor.grad.abs().mean(dim=1).squeeze().numpy()
        back_grads = back_tensor.grad.abs().mean(dim=1).squeeze().numpy()
        
        # Analyze gradient patterns
        front_importance = front_grads.mean()
        back_importance = back_grads.mean()
        
        print(f"   Front Image Importance: {front_importance:.4f}")
        print(f"   Back Image Importance: {back_importance:.4f}")
        
        if front_importance > back_importance * 1.5:
            print(f"   🎭 Model primarily focuses on FRONT damage/condition")
        elif back_importance > front_importance * 1.5:
            print(f"   🔄 Model primarily focuses on BACK damage/condition")
        else:
            print(f"   ⚖️  Model considers both front AND back equally")
    
    def _generate_attention_maps(self, front_img, back_img, front_tensor, back_tensor, outputs, predicted_grade):
        """Generate and save attention heatmaps"""
        
        try:
            # Create attention visualizations directory
            os.makedirs("attention_maps", exist_ok=True)
            
            # Get feature maps from model (simplified approach)
            predicted_class = outputs.argmax(dim=1).item()
            class_score = outputs[0, predicted_class]
            
            # Compute gradients for attention
            front_tensor.grad = None
            back_tensor.grad = None
            class_score.backward(retain_graph=True)
            
            if front_tensor.grad is not None:
                front_attention = front_tensor.grad.abs().mean(dim=1).squeeze().numpy()
                back_attention = back_tensor.grad.abs().mean(dim=1).squeeze().numpy()
                
                # Save attention maps
                front_path = f"attention_maps/front_attention_psa{predicted_grade}.png"
                back_path = f"attention_maps/back_attention_psa{predicted_grade}.png"
                
                # Convert attention to heatmap
                self._save_attention_heatmap(np.array(front_img), front_attention, front_path)
                self._save_attention_heatmap(np.array(back_img), back_attention, back_path)
                
                print(f"   🗺️  Attention maps saved:")
                print(f"      Front: {front_path}")
                print(f"      Back: {back_path}")
            else:
                print(f"   ⚠️  Could not generate attention maps (no gradients)")
                
        except Exception as e:
            print(f"   ⚠️  Attention map generation failed: {e}")
    
    def _save_attention_heatmap(self, image, attention, save_path):
        """Save attention heatmap overlay"""
        
        # Resize attention to match image
        attention_resized = cv2.resize(attention, (image.shape[1], image.shape[0]))
        
        # Normalize attention
        attention_norm = (attention_resized - attention_resized.min()) / (attention_resized.max() - attention_resized.min())
        
        # Create heatmap
        heatmap = plt.cm.jet(attention_norm)[:, :, :3]
        
        # Overlay on original image
        overlay = 0.6 * image/255.0 + 0.4 * heatmap
        overlay = np.clip(overlay, 0, 1)
        
        # Save
        plt.imsave(save_path, overlay)
    
    def _suggest_improvements(self, grade_probs, predicted_grade):
        """Suggest what would improve the grade"""
        
        psa_10_prob = grade_probs[9]
        
        if predicted_grade == 10:
            print(f"   ✨ Already predicted as PSA 10!")
        elif predicted_grade == 9:
            deficit = grade_probs[9] - grade_probs[8]
            print(f"   📈 To reach PSA 10, need {-deficit:.1%} more 'perfect' features")
            print(f"   🔍 Likely issues: Minor centering, tiny surface wear, or edge imperfection")
        elif predicted_grade == 8:
            print(f"   📈 To reach PSA 10: {grade_probs[9] - grade_probs[7]:.1%} improvement needed")
            print(f"   🔍 Likely issues: Centering problems, corner/edge wear, or surface scratches")
        else:
            print(f"   📈 Significant improvement needed for PSA 10")
            print(f"   🔍 Multiple condition issues detected")
        
        # Specific recommendations based on probability distribution
        if psa_10_prob > 0.3:
            print(f"   💡 Close to PSA 10 - minor condition improvement could help")
        elif psa_10_prob > 0.15:
            print(f"   💡 Moderate potential - address main condition issues")
        else:
            print(f"   💡 Lower potential - multiple condition problems exist")
    
    def _generate_explanation(self, grade_probs, predicted_grade):
        """Generate human-readable explanation"""
        
        psa_10_prob = grade_probs[9]
        reasons = []
        
        if predicted_grade < 10:
            if psa_10_prob < 0.2:
                reasons.append("Model detects significant condition issues preventing PSA 10")
            elif psa_10_prob < 0.4:
                reasons.append("Model sees minor imperfections that impact perfect grade")
            else:
                reasons.append("Very close to PSA 10, but model detects subtle issues")
        
        if grade_probs[predicted_grade-1] > 0.4:
            reasons.append(f"High confidence in PSA {predicted_grade}")
        else:
            reasons.append(f"Moderate confidence in PSA {predicted_grade}")
        
        return " | ".join(reasons)


def main():
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python explainable_predictor.py <front_img> <back_img>")
        print("Example: python explainable_predictor.py front.jpg back.jpg")
        return
    
    front_img_path = sys.argv[1]
    back_img_path = sys.argv[2]
    
    if not os.path.exists(front_img_path) or not os.path.exists(back_img_path):
        print(f"❌ Image files not found!")
        return
    
    predictor = ExplainablePSAPredictor()
    result = predictor.predict_with_explanation(front_img_path, back_img_path)
    
    print(f"\\n🎯 FINAL EXPLANATION:")
    print(f"   {result['explanation']}")


if __name__ == "__main__":
    main()