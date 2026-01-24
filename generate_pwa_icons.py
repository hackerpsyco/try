#!/usr/bin/env python3
"""
Generate PWA icons in all required sizes from a base image.
Requires: Pillow (PIL)

Usage:
    python generate_pwa_icons.py <source_image> [output_dir]

Example:
    python generate_pwa_icons.py static/images/wes-logo.jpg static/icons/
"""

import sys
import os
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is not installed. Install it with: pip install Pillow")
    sys.exit(1)


def generate_icons(source_image, output_dir="static/icons"):
    """Generate PWA icons in all required sizes."""
    
    # Required icon sizes for PWA
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Open the source image
        img = Image.open(source_image)
        print(f"✓ Opened source image: {source_image}")
        print(f"  Original size: {img.size}")
        
        # Convert to RGBA if needed (for transparency support)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            print(f"✓ Converted to RGBA mode")
        
        # Generate icons for each size
        for size in sizes:
            # Create a square canvas with white background
            canvas = Image.new('RGBA', (size, size), (255, 255, 255, 255))
            
            # Resize image to fit in the canvas (with padding)
            img_resized = img.copy()
            img_resized.thumbnail((size - 10, size - 10), Image.Resampling.LANCZOS)
            
            # Calculate position to center the image
            x = (size - img_resized.width) // 2
            y = (size - img_resized.height) // 2
            
            # Paste the resized image onto the canvas
            canvas.paste(img_resized, (x, y), img_resized)
            
            # Save the icon
            output_path = os.path.join(output_dir, f"icon-{size}x{size}.png")
            canvas.save(output_path, 'PNG', optimize=True)
            print(f"✓ Generated: {output_path} ({size}x{size})")
        
        print(f"\n✓ All icons generated successfully in {output_dir}/")
        print("\nNext steps:")
        print("1. Run: python manage.py collectstatic --noinput --clear")
        print("2. Run: sudo systemctl restart nginx")
        print("3. Clear browser cache and hard reload")
        
    except FileNotFoundError:
        print(f"Error: Source image not found: {source_image}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_pwa_icons.py <source_image> [output_dir]")
        print("\nExample:")
        print("  python generate_pwa_icons.py static/images/wes-logo.jpg static/icons/")
        sys.exit(1)
    
    source = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "static/icons"
    
    generate_icons(source, output)
