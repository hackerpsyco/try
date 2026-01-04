#!/usr/bin/env python
"""
Tailwind CSS optimization script for CLAS Django application
This script optimizes Tailwind CSS for better performance
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None

def install_dependencies():
    """Install required npm dependencies"""
    print("📦 Installing Tailwind CSS dependencies...")
    
    theme_dir = Path("theme/static_src")
    if not theme_dir.exists():
        print("❌ Theme directory not found!")
        return False
    
    # Install dependencies
    commands = [
        "npm install tailwindcss@latest",
        "npm install @tailwindcss/forms@latest",
        "npm install @tailwindcss/typography@latest",
        "npm install autoprefixer@latest",
        "npm install postcss@latest",
        "npm install cssnano@latest"
    ]
    
    for cmd in commands:
        print(f"  Running: {cmd}")
        result = run_command(cmd, cwd=theme_dir)
        if result is None:
            print(f"  ❌ Failed to run: {cmd}")
            return False
        print(f"  ✅ Success")
    
    return True

def build_css(mode="development"):
    """Build Tailwind CSS"""
    print(f"🎨 Building Tailwind CSS in {mode} mode...")
    
    theme_dir = Path("theme/static_src")
    
    if mode == "production":
        cmd = "npm run build-prod"
        env = {"NODE_ENV": "production"}
    else:
        cmd = "npm run build"
        env = {"NODE_ENV": "development"}
    
    # Set environment variables
    current_env = os.environ.copy()
    current_env.update(env)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=theme_dir,
            env=current_env,
            capture_output=True,
            text=True,
            check=True
        )
        print("  ✅ CSS build successful!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ CSS build failed: {e.stderr}")
        return False

def analyze_css():
    """Analyze the generated CSS file"""
    print("📊 Analyzing generated CSS...")
    
    css_file = Path("theme/static/css/styles.css")
    if not css_file.exists():
        print("  ❌ CSS file not found!")
        return
    
    # Get file size
    file_size = css_file.stat().st_size
    file_size_kb = file_size / 1024
    file_size_mb = file_size_kb / 1024
    
    print(f"  📁 File size: {file_size_kb:.1f} KB ({file_size_mb:.2f} MB)")
    
    # Count CSS rules (approximate)
    with open(css_file, 'r', encoding='utf-8') as f:
        content = f.read()
        rule_count = content.count('{')
        print(f"  📏 Approximate CSS rules: {rule_count}")
    
    # Performance recommendations
    if file_size_kb > 500:
        print("  ⚠️  CSS file is large (>500KB). Consider:")
        print("     - Enabling purge in production")
        print("     - Removing unused Tailwind classes")
        print("     - Using more specific content paths")
    elif file_size_kb > 200:
        print("  ⚠️  CSS file is moderate (>200KB). Monitor for growth.")
    else:
        print("  ✅ CSS file size is optimal (<200KB)")

def optimize_templates():
    """Optimize template files for better Tailwind performance"""
    print("🔧 Optimizing templates...")
    
    template_dirs = [
        "Templates",
        "class/templates"
    ]
    
    optimizations = 0
    
    for template_dir in template_dirs:
        template_path = Path(template_dir)
        if not template_path.exists():
            continue
            
        # Find all HTML files
        html_files = list(template_path.rglob("*.html"))
        
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Optimize common patterns
                optimizations_made = []
                
                # Replace verbose class combinations with utility classes
                replacements = {
                    'class="flex items-center justify-center"': 'class="flex-center"',
                    'class="bg-white border border-gray-200 rounded-lg shadow-sm"': 'class="admin-card"',
                    'class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"': 'class="admin-button-primary"',
                    'class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"': 'class="admin-input"',
                }
                
                for old, new in replacements.items():
                    if old in content:
                        content = content.replace(old, new)
                        optimizations_made.append(f"Replaced verbose classes with utility class")
                
                # Save if changes were made
                if content != original_content:
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    optimizations += len(optimizations_made)
                    print(f"  ✅ Optimized: {html_file.name}")
                    
            except Exception as e:
                print(f"  ❌ Error optimizing {html_file}: {e}")
    
    print(f"  📈 Total optimizations made: {optimizations}")

def create_build_script():
    """Create a build script for easy CSS compilation"""
    print("📝 Creating build script...")
    
    build_script = """#!/bin/bash
# Tailwind CSS Build Script for CLAS

echo "🚀 Building Tailwind CSS for CLAS..."

# Navigate to theme directory
cd theme/static_src

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build CSS based on environment
if [ "$1" = "prod" ] || [ "$1" = "production" ]; then
    echo "🏗️  Building for production..."
    NODE_ENV=production npm run build-prod
else
    echo "🏗️  Building for development..."
    npm run build
fi

echo "✅ Build complete!"

# Show file size
if [ -f "../css/styles.css" ]; then
    echo "📊 CSS file size:"
    ls -lh ../css/styles.css | awk '{print $5}'
fi
"""
    
    with open("build_tailwind.sh", "w") as f:
        f.write(build_script)
    
    # Make executable on Unix systems
    try:
        os.chmod("build_tailwind.sh", 0o755)
    except:
        pass
    
    print("  ✅ Created build_tailwind.sh")

def main():
    """Main optimization function"""
    print("🎨 CLAS Tailwind CSS Optimization Tool")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("❌ Please run this script from the Django project root directory")
        sys.exit(1)
    
    # Get mode from command line argument
    mode = "development"
    if len(sys.argv) > 1:
        if sys.argv[1] in ["prod", "production"]:
            mode = "production"
    
    print(f"🔧 Mode: {mode}")
    print()
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    print()
    
    # Step 2: Optimize templates
    optimize_templates()
    print()
    
    # Step 3: Build CSS
    if not build_css(mode):
        print("❌ Failed to build CSS")
        sys.exit(1)
    
    print()
    
    # Step 4: Analyze results
    analyze_css()
    print()
    
    # Step 5: Create build script
    create_build_script()
    print()
    
    print("🎉 Tailwind CSS optimization complete!")
    print()
    print("📋 Next steps:")
    print("  1. Run 'python manage.py collectstatic' to collect static files")
    print("  2. Test your admin interface for any styling issues")
    print("  3. Use './build_tailwind.sh prod' for production builds")
    print("  4. Monitor CSS file size and performance")

if __name__ == "__main__":
    main()