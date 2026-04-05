#!/bin/bash
# setup_and_train.sh - Complete setup script for PSA grade prediction

set -e  # Exit on any error

echo "🚀 PSA Grade Prediction - Setup and Training"
echo "=============================================="

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version)
echo "   $python_version"

# Check if we're in the right directory
if [ ! -f "output.filtered.json" ]; then
    echo "❌ Error: output.filtered.json not found in current directory"
    echo "   Make sure you're in the scripts/ml directory"
    exit 1
fi

# Install requirements
echo ""
echo "📦 Installing Python packages..."
pip3 install -r requirements.txt

# Check if dataset exists
if [ ! -d "dataset" ]; then
    echo ""
    echo "📁 Dataset not found. Preparing dataset from JSON data..."
    
    # Ask user about dataset size for testing
    echo ""
    echo "🤔 How many images per grade would you like to download?"
    echo "   - For quick testing: 10-20 images per grade (fast)"
    echo "   - For better results: 50-100 images per grade (medium)"  
    echo "   - For full dataset: all available images (slow)"
    echo ""
    read -p "Enter max images per grade (leave empty for all): " max_images
    
    if [ -z "$max_images" ]; then
        echo "📥 Downloading all available images..."
        python3 prepare_dataset.py
    else
        echo "📥 Downloading up to $max_images images per grade..."
        python3 prepare_dataset.py --max-per-grade="$max_images"
    fi
    
    if [ $? -ne 0 ]; then
        echo "❌ Dataset preparation failed!"
        exit 1
    fi
else
    echo "✅ Dataset directory found"
fi

# Check dataset contents and ask about combined images
echo ""
echo "📊 Dataset summary:"
front_count=0
back_count=0
for grade_dir in dataset/*; do
    if [ -d "$grade_dir" ]; then
        grade=$(basename "$grade_dir")
        front_images=$(find "$grade_dir" -name "*_front.jpg" | wc -l)
        back_images=$(find "$grade_dir" -name "*_back.jpg" | wc -l)
        total_images=$(find "$grade_dir" -name "*.jpg" | wc -l)
        echo "   Grade $grade: $total_images images ($front_images front, $back_images back)"
        front_count=$((front_count + front_images))
        back_count=$((back_count + back_images))
    fi
done

echo "   Total: $((front_count + back_count)) images ($front_count front, $back_count back)"

# Ask about training mode if both front and back images exist
if [ "$back_count" -gt 0 ] && [ "$front_count" -gt 0 ]; then
    echo ""
    echo "🎯 Both front and back images detected!"
    echo "   Training options:"
    echo "   1. Front images only (faster, simpler)"
    echo "   2. Combined front+back images (more accurate PSA grading)"
    echo ""
    read -p "Choose training mode (1 or 2): " training_mode
    
    if [ "$training_mode" = "2" ]; then
        echo ""
        echo "📐 Creating combined front+back images..."
        python3 combine_images.py --dataset dataset --output dataset_combined
        
        if [ $? -ne 0 ]; then
            echo "❌ Image combination failed!"
            exit 1
        fi
        
        echo "🎯 Training on combined front+back images..."
        python3 ml_starter.py --combined
    else
        echo "🎯 Training on front images only..."
        python3 ml_starter.py
    fi
else
    if [ "$back_count" -eq 0 ]; then
        echo ""
        echo "ℹ️  Only front images found - training on front images only"
    fi
    
    # Start standard training
    echo ""
    echo "🎯 Starting model training..."
    echo "   This may take a while depending on your hardware..."
    echo ""
    
    python3 ml_starter.py
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Training completed successfully!"
    echo ""
    echo "📄 Generated files:"
    echo "   models/best_psa_grade_model.pth - Trained model"
    echo "   logs/evaluation_results.json - Performance metrics"
    echo "   logs/confusion_matrix.png - Confusion matrix visualization"
    echo "   logs/training_history.png - Training progress plots"
    
    if [ -d "dataset_combined" ]; then
        echo "   dataset_combined/ - Combined front+back images"
    fi
    
    echo ""
    echo "💡 To make predictions on new images:"
    if [ "$training_mode" = "2" ] || [ -d "dataset_combined" ]; then
        echo "   # For combined front+back images:"
        echo "   from ml_starter import predict_image, PSAGradeConfig"
        echo "   config = PSAGradeConfig(use_combined_images=True)"
        echo "   grade, confidence = predict_image('models/best_psa_grade_model.pth', 'combined_card.jpg', config)"
    else
        echo "   # For single card images:"
        echo "   from ml_starter import predict_image, PSAGradeConfig"
        echo "   config = PSAGradeConfig()"
        echo "   grade, confidence = predict_image('models/best_psa_grade_model.pth', 'card.jpg', config)"
    fi
    echo "   print(f'Predicted PSA Grade: {grade} (Confidence: {confidence:.2f})')"
else
    echo ""
    echo "❌ Training failed! Check the error messages above."
    exit 1
fi