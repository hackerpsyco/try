#!/usr/bin/env python
"""
Quick setup script for Tailwind CSS optimization in CLAS
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, cwd=None, check=True):
    """Run a command and return success status"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def main():
    print("🚀 Setting up Tailwind CSS optimization for CLAS...")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("❌ Please run this script from the Django project root")
        sys.exit(1)
    
    # Step 1: Check Node.js installation
    print("1️⃣  Checking Node.js installation...")
    success, output = run_command("node --version", check=False)
    if not success:
        print("❌ Node.js not found. Please install Node.js first:")
        print("   https://nodejs.org/")
        sys.exit(1)
    else:
        print(f"✅ Node.js found: {output.strip()}")
    
    # Step 2: Navigate to theme directory and install dependencies
    theme_dir = Path("theme/static_src")
    if not theme_dir.exists():
        print("❌ Theme directory not found!")
        sys.exit(1)
    
    print("2️⃣  Installing npm dependencies...")
    
    # Create package.json if it doesn't exist
    package_json = theme_dir / "package.json"
    if not package_json.exists():
        print("❌ package.json not found in theme/static_src/")
        print("   Please ensure the optimization files were created correctly")
        sys.exit(1)
    
    # Install dependencies
    success, output = run_command("npm install", cwd=theme_dir)
    if not success:
        print(f"❌ Failed to install npm dependencies: {output}")
        sys.exit(1)
    else:
        print("✅ npm dependencies installed successfully")
    
    # Step 3: Build CSS for development
    print("3️⃣  Building Tailwind CSS...")
    success, output = run_command("npm run build", cwd=theme_dir)
    if not success:
        print(f"❌ Failed to build CSS: {output}")
        print("   Trying alternative build method...")
        
        # Try direct tailwindcss command
        success, output = run_command(
            "npx tailwindcss -i ./src/styles.css -o ../css/styles.css --minify",
            cwd=theme_dir
        )
        if not success:
            print(f"❌ Alternative build also failed: {output}")
            sys.exit(1)
    
    print("✅ CSS built successfully")
    
    # Step 4: Check CSS file
    css_file = Path("theme/static/css/styles.css")
    if css_file.exists():
        file_size = css_file.stat().st_size / 1024  # KB
        print(f"📊 CSS file size: {file_size:.1f} KB")
        
        if file_size > 500:
            print("⚠️  CSS file is large. Consider running production build:")
            print("   npm run build-prod")
        else:
            print("✅ CSS file size looks good")
    else:
        print("⚠️  CSS file not found, but build reported success")
    
    # Step 5: Run Django collectstatic
    print("4️⃣  Collecting static files...")
    success, output = run_command("python manage.py collectstatic --noinput")
    if not success:
        print(f"⚠️  collectstatic failed: {output}")
        print("   You may need to run this manually later")
    else:
        print("✅ Static files collected")
    
    # Step 6: Make build script executable
    build_script = Path("build_tailwind.sh")
    if build_script.exists():
        try:
            os.chmod(build_script, 0o755)
            print("✅ Build script made executable")
        except:
            print("⚠️  Could not make build script executable (Windows?)")
    
    print("\n🎉 Tailwind CSS optimization setup complete!")
    print("\n📋 What's been set up:")
    print("  ✅ Optimized Tailwind configuration")
    print("  ✅ Performance-focused CSS build process")
    print("  ✅ Custom utility classes for admin interface")
    print("  ✅ Optimized base template with critical CSS")
    print("  ✅ Build scripts and management commands")
    
    print("\n🚀 Next steps:")
    print("  1. Test your admin interface: python manage.py runserver")
    print("  2. For production builds: ./build_tailwind.sh prod")
    print("  3. Monitor CSS performance: python manage.py optimize_tailwind --analyze")
    print("  4. Read the optimization guide: TAILWIND_OPTIMIZATION_GUIDE.md")
    
    print("\n💡 Quick commands:")
    print("  • Development build: npm run build (in theme/static_src/)")
    print("  • Production build: npm run build-prod (in theme/static_src/)")
    print("  • Analyze CSS: python manage.py optimize_tailwind --analyze")
    print("  • Optimize templates: python optimize_tailwind.py")

if __name__ == "__main__":
    main()