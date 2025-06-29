#!/bin/bash

echo "Installing OCR dependencies for license scanning..."

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS. Installing Tesseract via Homebrew..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install Tesseract OCR
    echo "Installing Tesseract OCR..."
    brew install tesseract
    
    # Install additional language data for better OCR
    echo "Installing additional Tesseract language data..."
    brew install tesseract-lang
    
    echo "✅ Tesseract OCR installed successfully!"
    echo "Tesseract version: $(tesseract --version | head -n 1)"
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux. Installing Tesseract via apt..."
    
    # Update package list
    sudo apt update
    
    # Install Tesseract OCR
    sudo apt install -y tesseract-ocr
    
    # Install additional language data
    sudo apt install -y tesseract-ocr-eng
    
    echo "✅ Tesseract OCR installed successfully!"
    echo "Tesseract version: $(tesseract --version | head -n 1)"
    
else
    echo "❌ Unsupported operating system: $OSTYPE"
    echo "Please install Tesseract OCR manually:"
    echo "  - macOS: brew install tesseract"
    echo "  - Ubuntu/Debian: sudo apt install tesseract-ocr"
    echo "  - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
    exit 1
fi

echo ""
echo "🎉 OCR setup complete! You can now use the license scanner."
echo "To test, run: python3 -c \"from license_scanner import LicenseScanner; print('License scanner ready!')\"" 