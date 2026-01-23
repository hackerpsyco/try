#!/usr/bin/env python3
"""
Script to create PWA icons for the CLAS application.
Creates 192x192 and 512x512 PNG icons with a simple design.
"""

try:
    from PIL import Image, ImageDraw
    import os
    
    # Create static/images directory if it doesn't exist
    os.makedirs('static/images', exist_ok=True)
    
    # Define colors
    BLUE = '#3b82f6'
    WHITE = '#ffffff'
    
    # Create 192x192 icon
    img_192 = Image.new('RGB', (192, 192), WHITE)
    draw_192 = ImageDraw.Draw(img_192)
    
    # Draw blue background
    draw_192.rectangle([0, 0, 192, 192], fill=BLUE)
    
    # Draw white "C" for CLAS
    draw_192.text((60, 50), "C", fill=WHITE, font=None)
    
    img_192.save('static/images/icon-192.png')
    print("✓ Created icon-192.png")
    
    # Create 512x512 icon
    img_512 = Image.new('RGB', (512, 512), WHITE)
    draw_512 = ImageDraw.Draw(img_512)
    
    # Draw blue background
    draw_512.rectangle([0, 0, 512, 512], fill=BLUE)
    
    # Draw white "CLAS" text
    draw_512.text((150, 180), "CLAS", fill=WHITE, font=None)
    
    img_512.save('static/images/icon-512.png')
    print("✓ Created icon-512.png")
    
    # Create maskable icon (same as 192x192 for now)
    img_maskable = Image.new('RGB', (192, 192), WHITE)
    draw_maskable = ImageDraw.Draw(img_maskable)
    
    # Draw blue background
    draw_maskable.rectangle([0, 0, 192, 192], fill=BLUE)
    
    # Draw white circle in center
    draw_maskable.ellipse([48, 48, 144, 144], fill=WHITE)
    
    img_maskable.save('static/images/icon-maskable.png')
    print("✓ Created icon-maskable.png")
    
    # Create screenshot
    img_screenshot = Image.new('RGB', (540, 720), WHITE)
    draw_screenshot = ImageDraw.Draw(img_screenshot)
    
    # Draw blue header
    draw_screenshot.rectangle([0, 0, 540, 100], fill=BLUE)
    
    # Draw white text
    draw_screenshot.text((50, 30), "CLAS Dashboard", fill=WHITE, font=None)
    
    img_screenshot.save('static/images/screenshot-1.png')
    print("✓ Created screenshot-1.png")
    
    print("\n✅ All PWA icons created successfully!")
    
except ImportError:
    print("⚠️  PIL (Pillow) not installed. Creating placeholder files instead...")
    
    # Create placeholder files
    os.makedirs('static/images', exist_ok=True)
    
    # Create empty PNG files as placeholders
    for filename in ['icon-192.png', 'icon-512.png', 'icon-maskable.png', 'screenshot-1.png']:
        with open(f'static/images/{filename}', 'wb') as f:
            # Write minimal PNG header
            f.write(b'\x89PNG\r\n\x1a\n')
        print(f"✓ Created placeholder {filename}")
    
    print("\n⚠️  Placeholder icons created. Please replace with actual images.")
