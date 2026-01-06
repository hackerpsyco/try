#!/usr/bin/env python
"""
Test script to debug curriculum content loading
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CLAS.settings')
django.setup()

# Import after Django setup
import importlib
curriculum_module = importlib.import_module('class.services.curriculum_content_resolver')
CurriculumContentResolver = curriculum_module.CurriculumContentResolver

def test_curriculum_loading():
    """Test curriculum content loading"""
    print("🧪 Testing Curriculum Content Loading")
    print("=" * 50)
    
    resolver = CurriculumContentResolver()
    
    # Test English Day 1
    print("\n1. Testing English Day 1...")
    try:
        result = resolver.resolve_content(1, 'english')
        print(f"✅ Source: {result.source}")
        print(f"✅ Content length: {len(result.content)} chars")
        
        if "Day 1 Content Not Found" in result.content:
            print("❌ Day 1 content not found in English file")
            print("First 500 chars of content:")
            print(result.content[:500])
        else:
            print("✅ Day 1 content found successfully")
            
    except Exception as e:
        print(f"❌ Error loading English Day 1: {e}")
    
    # Test Hindi Day 1
    print("\n2. Testing Hindi Day 1...")
    try:
        result = resolver.resolve_content(1, 'hindi')
        print(f"✅ Source: {result.source}")
        print(f"✅ Content length: {len(result.content)} chars")
        
        if "Day 1 Content Not Found" in result.content:
            print("❌ Day 1 content not found in Hindi file")
            print("First 500 chars of content:")
            print(result.content[:500])
        else:
            print("✅ Day 1 content found successfully")
            
    except Exception as e:
        print(f"❌ Error loading Hindi Day 1: {e}")
    
    # Test file existence
    print("\n3. Testing file existence...")
    from pathlib import Path
    from django.conf import settings
    
    english_path = Path(settings.BASE_DIR) / 'Templates/admin/session/English_ ALL DAYS.html'
    hindi_path = Path(settings.BASE_DIR) / 'Templates/admin/session/Hindi_ ALL DAYS.html'
    
    print(f"English file exists: {english_path.exists()}")
    print(f"Hindi file exists: {hindi_path.exists()}")
    
    if english_path.exists():
        with open(english_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"English file size: {len(content)} chars")
            if "Day 1" in content:
                print("✅ 'Day 1' pattern found in English file")
            else:
                print("❌ 'Day 1' pattern NOT found in English file")
    
    if hindi_path.exists():
        with open(hindi_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Hindi file size: {len(content)} chars")
            if "दिन 1" in content:
                print("✅ 'दिन 1' pattern found in Hindi file")
            else:
                print("❌ 'दिन 1' pattern NOT found in Hindi file")

if __name__ == "__main__":
    test_curriculum_loading()