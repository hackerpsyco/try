#!/usr/bin/env python
"""
Simple script to clear curriculum cache after fixing image paths.
Run this after updating the curriculum content resolver.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CLAS.settings')
django.setup()

from django.core.cache import cache
from class.services.curriculum_content_resolver import CurriculumContentResolver

def clear_curriculum_cache():
    """Clear all curriculum content cache."""
    try:
        resolver = CurriculumContentResolver()
        resolver.invalidate_cache()
        print("✅ Curriculum cache cleared successfully!")
        
        # Also clear any other related cache keys
        cache_keys_to_clear = []
        for lang in ['english', 'hindi']:
            for day in range(1, 151):
                cache_keys_to_clear.append(f"curriculum_content:{lang}:{day}")
        
        cache.delete_many(cache_keys_to_clear)
        print(f"✅ Cleared {len(cache_keys_to_clear)} cache keys")
        
    except Exception as e:
        print(f"❌ Error clearing cache: {str(e)}")

if __name__ == "__main__":
    clear_curriculum_cache()