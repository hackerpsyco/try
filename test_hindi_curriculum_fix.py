#!/usr/bin/env python3
"""
Quick test script to verify Hindi curriculum content parsing fix.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CLAS.settings')
django.setup()

from class.services.curriculum_content_resolver import CurriculumContentResolver

def test_hindi_curriculum_parsing():
    """Test that Hindi curriculum content can be parsed correctly."""
    
    print("Testing Hindi curriculum content parsing...")
    
    resolver = CurriculumContentResolver()
    
    # Test Hindi content loading
    print("\n1. Testing Hindi Day 1 content loading...")
    try:
        result = resolver.resolve_content(day=1, language='hindi')
        print(f"   Source: {result.source}")
        print(f"   Content length: {len(result.content)} characters")
        
        if "दिन 1" in result.content or "Day 1" in result.content:
            print("   ✅ SUCCESS: Day 1 content found!")
        elif "Content Not Found" in result.content:
            print("   ❌ FAILED: Day 1 content not found")
        else:
            print("   ⚠️  PARTIAL: Content loaded but day pattern unclear")
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
    
    # Test Hindi Day 2 content loading
    print("\n2. Testing Hindi Day 2 content loading...")
    try:
        result = resolver.resolve_content(day=2, language='hindi')
        print(f"   Source: {result.source}")
        print(f"   Content length: {len(result.content)} characters")
        
        if "दिन 2" in result.content or "Day 2" in result.content:
            print("   ✅ SUCCESS: Day 2 content found!")
        elif "Content Not Found" in result.content:
            print("   ❌ FAILED: Day 2 content not found")
        else:
            print("   ⚠️  PARTIAL: Content loaded but day pattern unclear")
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
    
    # Test English content still works
    print("\n3. Testing English Day 1 content loading (should still work)...")
    try:
        result = resolver.resolve_content(day=1, language='english')
        print(f"   Source: {result.source}")
        print(f"   Content length: {len(result.content)} characters")
        
        if "Day 1" in result.content:
            print("   ✅ SUCCESS: English Day 1 content found!")
        elif "Content Not Found" in result.content:
            print("   ❌ FAILED: English Day 1 content not found")
        else:
            print("   ⚠️  PARTIAL: Content loaded but day pattern unclear")
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
    
    # Test availability check
    print("\n4. Testing content availability check...")
    try:
        hindi_status = resolver.check_content_availability(day=1, language='hindi')
        english_status = resolver.check_content_availability(day=1, language='english')
        
        print(f"   Hindi Day 1 available: {hindi_status.is_available} (source: {hindi_status.source})")
        print(f"   English Day 1 available: {english_status.is_available} (source: {english_status.source})")
        
        if hindi_status.is_available and english_status.is_available:
            print("   ✅ SUCCESS: Both languages show as available!")
        else:
            print("   ❌ ISSUE: One or both languages not available")
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_hindi_curriculum_parsing()
    print("\nTest completed!")