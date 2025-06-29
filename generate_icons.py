#!/usr/bin/env python3
"""
Generate placeholder icons for RapidCare PWA
This creates simple colored squares as placeholders for the app icons
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    """Create a simple icon with the RapidCare branding"""
    # Create image with red background (RapidCare theme)
    img = Image.new('RGB', (size, size), color='#dc2626')
    draw = ImageDraw.Draw(img)
    
    # Add a white cross symbol (medical theme)
    cross_size = size // 3
    cross_thickness = max(1, size // 20)
    
    # Vertical line of cross
    x1 = size // 2 - cross_thickness // 2
    x2 = size // 2 + cross_thickness // 2
    y1 = size // 2 - cross_size // 2
    y2 = size // 2 + cross_size // 2
    
    draw.rectangle([x1, y1, x2, y2], fill='white')
    
    # Horizontal line of cross
    x1 = size // 2 - cross_size // 2
    x2 = size // 2 + cross_size // 2
    y1 = size // 2 - cross_thickness // 2
    y2 = size // 2 + cross_thickness // 2
    
    draw.rectangle([x1, y1, x2, y2], fill='white')
    
    # Save the icon
    img.save(filename, 'PNG')
    print(f"Created icon: {filename}")

def main():
    """Generate all required icon sizes"""
    # Ensure images directory exists
    os.makedirs('static/images', exist_ok=True)
    
    # Icon sizes needed for PWA
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    for size in sizes:
        filename = f'static/images/icon-{size}x{size}.png'
        create_icon(size, filename)
    
    # Create a simple screenshot placeholder
    create_screenshot_placeholder()

def create_screenshot_placeholder():
    """Create placeholder screenshots for the PWA manifest"""
    # Wide screenshot (desktop)
    wide_img = Image.new('RGB', (1280, 720), color='#f9fafb')
    draw = ImageDraw.Draw(wide_img)
    
    # Add some placeholder content
    draw.rectangle([50, 50, 1230, 670], outline='#dc2626', width=3)
    draw.text((640, 360), "RapidCare Desktop Interface", fill='#1f2937', anchor='mm')
    
    wide_img.save('static/images/screenshot-wide.png', 'PNG')
    print("Created screenshot: static/images/screenshot-wide.png")
    
    # Narrow screenshot (mobile)
    narrow_img = Image.new('RGB', (750, 1334), color='#f9fafb')
    draw = ImageDraw.Draw(narrow_img)
    
    # Add some placeholder content
    draw.rectangle([25, 25, 725, 1309], outline='#dc2626', width=3)
    draw.text((375, 667), "RapidCare Mobile Interface", fill='#1f2937', anchor='mm')
    
    narrow_img.save('static/images/screenshot-narrow.png', 'PNG')
    print("Created screenshot: static/images/screenshot-narrow.png")

if __name__ == '__main__':
    main() 