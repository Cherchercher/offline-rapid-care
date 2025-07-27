import cv2
import numpy as np
import re
from PIL import Image
import pytesseract
from typing import Dict, Optional, List
import json
from datetime import datetime

class LicenseScanner:
    """Lightweight OCR-based driver's license scanner"""
    
    def __init__(self):
        """Initialize the license scanner"""
        # Configure pytesseract for better OCR
        self.tesseract_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%&*()_+-=[]{}|;:,.<>? '
        
        # Common patterns for license information
        self.patterns = {
            'name': [
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # First Last or First Middle Last
                r'NAME[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'([A-Z][A-Z\s]+)',  # ALL CAPS names
            ],
            'dob': [
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY or MM-DD-YYYY
                r'DOB[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'BIRTH[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
            'license_number': [
                r'(\d{7,12})',  # 7-12 digit numbers
                r'LIC[:\s]*(\d{7,12})',
                r'DL[:\s]*(\d{7,12})',
            ],
            'state': [
                r'([A-Z]{2})',  # Two letter state codes
                r'STATE[:\s]*([A-Z]{2})',
            ],
            'expires': [
                r'EXP[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'EXPIRES[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            ],
            'address': [
                r'(\d+\s+[A-Za-z\s]+(?:ST|STREET|AVE|AVENUE|RD|ROAD|BLVD|BOULEVARD|DR|DRIVE|LN|LANE|CT|COURT|PL|PLACE|WAY|CIR|CIRCLE|PKWY|PARKWAY|HWY|HIGHWAY)[,\s]+[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?)',
            ]
        }
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess the image for better OCR results"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Resize if too small
        h, w = gray.shape
        if w < 800:
            scale = 800 / w
            gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 31, 15)
        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast = clahe.apply(thresh)
        return contrast
    
    def extract_text(self, image: np.ndarray) -> str:
        """Extract text from image using OCR"""
        try:
            print("DEBUG: Starting text extraction...")
            
            # Preprocess image
            processed = self.preprocess_image(image)
            print(f"DEBUG: Image preprocessed, shape: {processed.shape}")
            
            # Extract text
            text = pytesseract.image_to_string(processed, config=self.tesseract_config)
            print(f"DEBUG: OCR completed, text length: {len(text)}")
            
            return text
        except Exception as e:
            print(f"OCR Error: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def extract_pdf417_data(self, image: np.ndarray) -> Optional[str]:
        """Attempt to extract PDF417 barcode data"""
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Look for rectangular patterns that might be PDF417
            # This is a simplified approach - in production you'd use a proper barcode library
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for rectangular contours that might be barcodes
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Minimum size for barcode
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # PDF417 barcodes are typically rectangular
                    if 2 < aspect_ratio < 10:
                        # Extract the region and try OCR
                        roi = gray[y:y+h, x:x+w]
                        barcode_text = pytesseract.image_to_string(roi, config='--oem 3 --psm 6')
                        if barcode_text.strip():
                            return barcode_text.strip()
            
            return None
            
        except Exception as e:
            print(f"PDF417 extraction error: {e}")
            return None
    
    def parse_license_data(self, text: str) -> Dict:
        """Parse extracted text to find license information"""
        data = {}
        
        # Clean up the text
        text = text.upper().replace('\n', ' ').replace('_', ' ')
        print(f"DEBUG: Cleaned text: {text}")
        
        # Name patterns - look for NAME: or similar patterns
        name_patterns = [
            r'NAME[:\s]*([A-Z][A-Z\s]+?)(?=\s*(?:DOB|BIRTH|LICENSE|DL|ID|ADDRESS|EXP|CLASS))',
            r'([A-Z][A-Z\s]{2,20})(?=\s*(?:DOB|BIRTH|LICENSE|DL|ID|ADDRESS|EXP|CLASS))',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                if len(name) > 3 and not name.isdigit():
                    data['name'] = name
                    print(f"DEBUG: Found name: {name}")
                    break
        
        # Date of birth patterns
        dob_patterns = [
            r'DOB[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'BIRTH[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        ]
        
        for pattern in dob_patterns:
            match = re.search(pattern, text)
            if match:
                dob = match.group(1)
                data['date_of_birth'] = dob
                print(f"DEBUG: Found DOB: {dob}")
                break
        
        # License number patterns
        license_patterns = [
            r'LICENSE[:\s]*(\d{7,12})',
            r'DL[:\s]*(\d{7,12})',
            r'ID[:\s]*(\d{7,12})',
            r'(\d{7,12})',
        ]
        
        for pattern in license_patterns:
            match = re.search(pattern, text)
            if match:
                license_num = match.group(1)
                data['license_number'] = license_num
                print(f"DEBUG: Found license: {license_num}")
                break
        
        # State patterns
        state_patterns = [
            r'STATE[:\s]*([A-Z]{2})',
            r'([A-Z]{2})\s*(?:DRIVER|LICENSE|ID)',
        ]
        
        for pattern in state_patterns:
            match = re.search(pattern, text)
            if match:
                state = match.group(1)
                data['state'] = state
                print(f"DEBUG: Found state: {state}")
                break
        
        return data
    
    def post_process_data(self, data: Dict) -> Dict:
        """Post-process extracted data for better accuracy"""
        processed = {}
        
        # Clean up name
        if 'name' in data:
            name = data['name']
            # Remove common prefixes/suffixes
            name = re.sub(r'\b(MR|MRS|MS|DR|JR|SR|III|IV|V)\b', '', name, flags=re.IGNORECASE)
            name = ' '.join(name.split())  # Normalize whitespace
            if len(name) > 2:
                processed['name'] = name.title()
        
        # Clean up DOB
        if 'dob' in data:
            dob = data['dob']
            # Standardize date format
            dob = re.sub(r'[-/]', '/', dob)
            processed['dob'] = dob
        
        # Clean up license number
        if 'license_number' in data:
            license_num = data['license_number']
            # Remove non-digits
            license_num = re.sub(r'\D', '', license_num)
            if len(license_num) >= 7:
                processed['license_number'] = license_num
        
        # Clean up state
        if 'state' in data:
            state = data['state']
            if len(state) == 2 and state.isalpha():
                processed['state'] = state.upper()
        
        # Clean up address
        if 'address' in data:
            address = data['address']
            # Basic cleaning
            address = re.sub(r'\s+', ' ', address)
            processed['address'] = address.strip()
        
        # Calculate age from DOB
        if processed.get('dob'):
            try:
                dob_date = datetime.strptime(processed['dob'], '%m/%d/%Y')
                age = datetime.now().year - dob_date.year
                if datetime.now().month < dob_date.month or (datetime.now().month == dob_date.month and datetime.now().day < dob_date.day):
                    age -= 1
                processed['age'] = str(age)
            except:
                processed['age'] = 'Unknown'
        
        return processed
    
    def scan_license(self, image: np.ndarray) -> Dict:
        """Main method to scan a driver's license image"""
        try:
            print("DEBUG: Starting license scan...")
            
            # Extract text using OCR
            text = self.extract_text(image)
            print(f"DEBUG: Extracted text length: {len(text)}")
            print(f"DEBUG: First 200 chars of text: {text[:200]}")
            
            # Extract PDF417 data if available
            pdf417_data = self.extract_pdf417_data(image)
            print(f"DEBUG: PDF417 data found: {pdf417_data is not None}")
            
            # Parse the extracted text
            license_data = self.parse_license_data(text)
            print(f"DEBUG: Parsed license data: {license_data}")
            
            # Add PDF417 data if found
            if pdf417_data:
                license_data['pdf417_data'] = pdf417_data
            
            # Add metadata
            license_data['scan_timestamp'] = datetime.now().isoformat()
            license_data['ocr_text'] = text[:500] + "..." if len(text) > 500 else text  # Truncate for display
            
            return {
                'success': True,
                'patient_info': license_data,
                'raw_text': text,
                'pdf417_found': pdf417_data is not None
            }
            
        except Exception as e:
            print(f"DEBUG: Exception in scan_license: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'patient_info': {},
                'raw_text': '',
                'pdf417_found': False
            }

# Example usage
if __name__ == "__main__":
    scanner = LicenseScanner()
    print("License Scanner initialized")
    print("Use scanner.scan_license(image) to process license images") 