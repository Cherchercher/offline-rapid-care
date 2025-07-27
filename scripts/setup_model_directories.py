#!/usr/bin/env python3
"""
Setup Model Directories
Helps users organize their model directories for both 2B and 4B models
"""

import os
import shutil
from pathlib import Path

def setup_model_directories():
    """Set up proper model directory structure"""
    
    print("🚀 Setting up Model Directories...")
    print("=" * 50)
    
    # Define paths
    current_model_path = "./models/gemma3n-local-e2b"
    model_2b_path = "./models/gemma3n-local-e2b"
    model_4b_path = "./models/gemma3n-local-e4b"
    
    # Create models directory
    os.makedirs("./models", exist_ok=True)
    
    # Check current state
    current_exists = os.path.exists(current_model_path)
    model_2b_exists = os.path.exists(model_2b_path)
    model_4b_exists = os.path.exists(model_4b_path)
    
    print(f"📁 Current Model Status:")
    print(f"   Existing gemma3n-local: {'✅ YES' if current_exists else '❌ NO'}")
    print(f"   Model 2B directory: {'✅ YES' if model_2b_exists else '❌ NO'}")
    print(f"   Model 4B directory: {'✅ YES' if model_4b_exists else '❌ NO'}")
    
    # Handle existing gemma3n-local directory
    if current_exists and not model_2b_exists:
        print(f"\n🔄 Renaming existing model to 2B...")
        try:
            shutil.move(current_model_path, model_2b_path)
            print(f"✅ Renamed {current_model_path} to {model_2b_path}")
        except Exception as e:
            print(f"❌ Failed to rename: {e}")
            return False
    elif current_exists and model_2b_exists:
        print(f"\n⚠️ Both {current_model_path} and {model_2b_path} exist.")
        print(f"   Please manually organize your models.")
        return False
    
    # Create directories if they don't exist
    if not model_2b_exists:
        os.makedirs(model_2b_path, exist_ok=True)
        print(f"📁 Created {model_2b_path}")
    
    if not model_4b_exists:
        os.makedirs(model_4b_path, exist_ok=True)
        print(f"📁 Created {model_4b_path}")
    
    # Check final state
    print(f"\n📋 Final Directory Structure:")
    print(f"   {model_2b_path}: {'✅ Ready' if os.path.exists(model_2b_path) else '❌ Missing'}")
    print(f"   {model_4b_path}: {'✅ Ready' if os.path.exists(model_4b_path) else '❌ Missing'}")
    
    # Provide next steps
    print(f"\n🎯 Next Steps:")
    
    if not os.path.exists(os.path.join(model_2b_path, "config.json")):
        print(f"   1. Download 2B model: python3 scripts/download_gemma_models.py --model 2b")
    
    if not os.path.exists(os.path.join(model_4b_path, "config.json")):
        print(f"   2. Download 4B model: python3 scripts/download_gemma_models.py --model 4b")
    
    print(f"   3. Test dynamic model manager: python3 scripts/dynamic_model_manager.py")
    print(f"   4. Update your app to use dynamic model selection")
    
    return True

def check_model_configuration():
    """Check current model configuration"""
    
    print("🔍 Checking Model Configuration...")
    print("=" * 50)
    
    # Check model_manager_pipeline.py
    pipeline_file = "model_manager_pipeline.py"
    if os.path.exists(pipeline_file):
        with open(pipeline_file, 'r') as f:
            content = f.read()
            
        if "./models/gemma3n-local-e2b" in content:
            print(f"✅ {pipeline_file} uses 2B model path")
        elif "./models/gemma3n-local-e4b" in content:
            print(f"✅ {pipeline_file} uses 4B model path")
        else:
            print(f"✅ {pipeline_file} uses dynamic model selection")
    else:
        print(f"❌ {pipeline_file} not found")
    
    # Check app.py
    app_file = "app.py"
    if os.path.exists(app_file):
        with open(app_file, 'r') as f:
            content = f.read()
            
        if "gemma3n-local-e2b" in content:
            print(f"⚠️ {app_file} still references old model path")
        else:
            print(f"✅ {app_file} uses updated model paths")

def main():
    """Main setup function"""
    
    print("🚀 RapidCare Model Directory Setup")
    print("=" * 50)
    
    # Setup directories
    success = setup_model_directories()
    
    if success:
        print(f"\n✅ Model directories setup complete!")
        
        # Check configuration
        check_model_configuration()
        
        print(f"\n💡 Configuration Options:")
        print(f"   1. Dynamic (Recommended): Automatically selects 2B or 4B based on load")
        print(f"   2. Static 2B: Always use 2B model (good for CPU environments)")
        print(f"   3. Static 4B: Always use 4B model (good for Jetson/GPU)")
        
        print(f"\n🎯 To use dynamic model selection:")
        print(f"   python3 scripts/dynamic_model_manager.py")
    else:
        print(f"\n❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    main() 