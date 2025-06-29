#!/usr/bin/env python3

import cv2
import numpy as np
from license_scanner import LicenseScanner

def test_ocr():
    """Test the OCR functionality"""
    print("Testing OCR functionality...")
    
    # Create a simple test image with text
    test_image = np.ones((200, 400, 3), dtype=np.uint8) * 255  # White background
    
    # Add some test text
    cv2.putText(test_image, "TEST LICENSE", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(test_image, "NAME: JOHN DOE", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(test_image, "DOB: 01/01/1990", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(test_image, "LICENSE: 123456789", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    print("Created test image with text")
    
    # Test the scanner
    scanner = LicenseScanner()
    result = scanner.scan_license(test_image)
    
    print(f"Scan result: {result}")
    
    if result['success']:
        print("✅ OCR test successful!")
        print(f"Extracted text: {result['raw_text'][:200]}...")
        print(f"Patient info: {result['patient_info']}")
    else:
        print("❌ OCR test failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_ocr() 