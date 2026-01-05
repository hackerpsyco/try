"""
Tests for CurriculumContentResolver service.
"""

import pytest
from django.test import TestCase
from django.core.cache import cache
from django.utils import timezone
from unittest.mock import patch, mock_open

from ..models import CurriculumSession, User, Role
from .curriculum_content_resolver import CurriculumContentResolver, ContentResult, AvailabilityStatus, ContentMetadata


class TestCurriculumContentResolver(TestCase):
    """Test cases for CurriculumContentResolver service."""
    
    def setUp(self):
        """Set up test data."""
        self.resolver = CurriculumContentResolver()
        
        # Create admin role
        self.admin_role, _ = Role.objects.get_or_create(
            id=0,
            defaults={'name': 'Admin'}
        )
        
        # Create test user
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role=self.admin_role,
            full_name='Test Admin'
        )
        
        # Create test curriculum session
        self.curriculum_session = CurriculumSession.objects.create(
            title='Test Session Day 1',
            day_number=1,
            language='english',
            content='<p>This is test content for day 1</p>',
            learning_objectives='Test learning objectives',
            activities={'warm_up': 'Test warm up activity'},
            resources={'video': 'http://example.com/video.mp4'},
            status='published',
            created_by=self.admin_user,
            is_active_for_facilitators=True
        )
        
        # Clear cache before each test
        cache.clear()
    
    def test_resolve_content_admin_managed(self):
        """Test resolving admin-managed content."""
        result = self.resolver.resolve_content(1, 'english')
        
        self.assertIsInstance(result, ContentResult)
        self.assertEqual(result.source, 'admin_managed')
        self.assertIsNotNone(result.curriculum_session)
        self.assertEqual(result.curriculum_session.id, self.curriculum_session.id)
        self.assertIn('Test Session Day 1', result.content)
        self.assertIn('Test learning objectives', result.content)
    
    def test_resolve_content_static_fallback(self):
        """Test resolving content with static fallback."""
        # Test with non-existent day
        with patch('builtins.open', mock_open(read_data='<h1>Day 99: Static Content</h1><p>Static content for day 99</p>')):
            with patch('pathlib.Path.exists', return_value=True):
                result = self.resolver.resolve_content(99, 'english')
                
                self.assertEqual(result.source, 'static_fallback')
                self.assertIsNone(result.curriculum_session)
                self.assertIn('Static content', result.content)
    
    def test_resolve_content_inactive_session(self):
        """Test resolving content when session is inactive."""
        # Make session inactive
        self.curriculum_session.is_active_for_facilitators = False
        self.curriculum_session.save()
        
        with patch('builtins.open', mock_open(read_data='<h1>Day 1: Static Content</h1>')):
            with patch('pathlib.Path.exists', return_value=True):
                result = self.resolver.resolve_content(1, 'english')
                
                self.assertEqual(result.source, 'static_fallback')
    
    def test_resolve_content_fallback_forced(self):
        """Test resolving content when fallback is forced."""
        # Force fallback to static
        self.curriculum_session.fallback_to_static = True
        self.curriculum_session.save()
        
        with patch('builtins.open', mock_open(read_data='<h1>Day 1: Static Content</h1>')):
            with patch('pathlib.Path.exists', return_value=True):
                result = self.resolver.resolve_content(1, 'english')
                
                self.assertEqual(result.source, 'static_fallback')
    
    def test_load_curriculum_content(self):
        """Test loading curriculum content directly."""
        content = self.resolver.load_curriculum_content(1, 'english')
        
        self.assertIsInstance(content, str)
        self.assertIn('Test Session Day 1', content)
    
    def test_check_content_availability_admin_managed(self):
        """Test checking availability for admin-managed content."""
        status = self.resolver.check_content_availability(1, 'english')
        
        self.assertIsInstance(status, AvailabilityStatus)
        self.assertTrue(status.is_available)
        self.assertEqual(status.source, 'admin_managed')
    
    def test_check_content_availability_static(self):
        """Test checking availability for static content."""
        with patch('pathlib.Path.exists', return_value=True):
            status = self.resolver.check_content_availability(99, 'english')
            
            self.assertTrue(status.is_available)
            self.assertEqual(status.source, 'static_fallback')
    
    def test_get_content_metadata_admin_managed(self):
        """Test getting metadata for admin-managed content."""
        metadata = self.resolver.get_content_metadata(1, 'english')
        
        self.assertIsInstance(metadata, ContentMetadata)
        self.assertEqual(metadata.source, 'admin_managed')
        self.assertEqual(metadata.title, 'Test Session Day 1')
        self.assertEqual(metadata.day_number, 1)
        self.assertEqual(metadata.language, 'english')
    
    def test_get_content_metadata_static(self):
        """Test getting metadata for static content."""
        metadata = self.resolver.get_content_metadata(99, 'english')
        
        self.assertEqual(metadata.source, 'static_fallback')
        self.assertEqual(metadata.day_number, 99)
        self.assertEqual(metadata.language, 'english')
        self.assertIsNone(metadata.last_updated)
    
    def test_cache_functionality(self):
        """Test that content is properly cached."""
        # First call should hit database
        result1 = self.resolver.resolve_content(1, 'english')
        
        # Second call should hit cache
        result2 = self.resolver.resolve_content(1, 'english')
        
        self.assertEqual(result1.content, result2.content)
        self.assertEqual(result1.source, result2.source)
    
    def test_invalidate_cache(self):
        """Test cache invalidation."""
        # Load content to cache it
        self.resolver.resolve_content(1, 'english')
        
        # Invalidate cache
        self.resolver.invalidate_cache(1, 'english')
        
        # Verify cache is cleared by checking cache directly
        cache_key = f"{self.resolver.cache_prefix}:english:1"
        self.assertIsNone(cache.get(cache_key))
    
    def test_usage_stats_update(self):
        """Test that usage statistics are updated."""
        initial_count = self.curriculum_session.usage_count
        initial_accessed = self.curriculum_session.last_accessed
        
        # Resolve content (should update stats)
        self.resolver.resolve_content(1, 'english')
        
        # Refresh from database
        self.curriculum_session.refresh_from_db()
        
        self.assertEqual(self.curriculum_session.usage_count, initial_count + 1)
        self.assertIsNotNone(self.curriculum_session.last_accessed)
        if initial_accessed:
            self.assertGreater(self.curriculum_session.last_accessed, initial_accessed)
    
    def test_format_activities(self):
        """Test activities formatting."""
        activities = {
            'warm_up': 'Test warm up',
            'main_activity': {
                'duration': '30 minutes',
                'description': 'Main learning activity'
            }
        }
        
        formatted = self.resolver._format_activities(activities)
        
        self.assertIn('Warm Up', formatted)
        self.assertIn('Test warm up', formatted)
        self.assertIn('Main Activity', formatted)
        self.assertIn('30 minutes', formatted)
    
    def test_format_resources(self):
        """Test resources formatting."""
        resources = {
            'video_link': 'http://example.com/video.mp4',
            'documents': {
                'worksheet': 'http://example.com/worksheet.pdf',
                'answer_key': '/static/answers.pdf'
            }
        }
        
        formatted = self.resolver._format_resources(resources)
        
        self.assertIn('href=', formatted)  # Should contain links
        self.assertIn('Video Link', formatted)
        self.assertIn('Documents', formatted)
    
    def test_error_handling(self):
        """Test error handling in content resolution."""
        # Test with invalid language
        result = self.resolver.resolve_content(1, 'invalid_language')
        
        # Should not crash and should return some content
        self.assertIsInstance(result, ContentResult)
        self.assertIsInstance(result.content, str)
    
    def tearDown(self):
        """Clean up after tests."""
        cache.clear()