"""
Tests for UsageTrackingService.
"""

import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import (
    CurriculumSession, CurriculumUsageLog, ClassSection, 
    School, Role, PlannedSession, User
)
from .usage_tracking_service import UsageTrackingService


class TestUsageTrackingService(TestCase):
    """Test cases for UsageTrackingService."""
    
    def setUp(self):
        """Set up test data."""
        # Create roles with specific IDs
        self.facilitator_role = Role.objects.create(id=2, name='Facilitator')
        self.admin_role = Role.objects.create(id=0, name='Admin')
        
        # Create users
        self.facilitator1 = User.objects.create_user(
            email='facilitator1@test.com',
            password='testpass123',
            role=self.facilitator_role,
            full_name='John Doe'
        )
        
        self.facilitator2 = User.objects.create_user(
            email='facilitator2@test.com',
            password='testpass123',
            role=self.facilitator_role,
            full_name='Jane Smith'
        )
        
        # Create school
        self.school = School.objects.create(
            name='Test School',
            udise='12345',
            block='Test Block',
            district='Test District',
            enrolled_students=100
        )
        
        # Create class sections
        self.class_section1 = ClassSection.objects.create(
            school=self.school,
            class_level='5',
            section='A'
        )
        
        self.class_section2 = ClassSection.objects.create(
            school=self.school,
            class_level='6',
            section='B'
        )
        
        # Create curriculum sessions
        self.curriculum_session1 = CurriculumSession.objects.create(
            day_number=1,
            language='english',
            title='Day 1 English Content',
            content='Test content for day 1',
            status='published',
            is_active_for_facilitators=True
        )
        
        self.curriculum_session2 = CurriculumSession.objects.create(
            day_number=2,
            language='hindi',
            title='Day 2 Hindi Content',
            content='Test content for day 2',
            status='published',
            is_active_for_facilitators=True
        )
        
        # Get existing planned sessions (auto-generated)
        self.planned_session1 = PlannedSession.objects.filter(
            class_section=self.class_section1,
            day_number=1
        ).first()
        
        self.planned_session2 = PlannedSession.objects.filter(
            class_section=self.class_section2,
            day_number=2
        ).first()
        
        self.service = UsageTrackingService()
    
    def test_log_curriculum_access(self):
        """Test logging curriculum access."""
        # Log access
        usage_log = self.service.log_curriculum_access(
            facilitator=self.facilitator1,
            curriculum_session=self.curriculum_session1,
            class_section=self.class_section1,
            planned_session=self.planned_session1,
            content_source='admin_managed'
        )
        
        # Verify log was created
        self.assertIsNotNone(usage_log)
        self.assertEqual(usage_log.facilitator, self.facilitator1)
        self.assertEqual(usage_log.curriculum_session, self.curriculum_session1)
        self.assertEqual(usage_log.class_section, self.class_section1)
        self.assertEqual(usage_log.content_source, 'admin_managed')
    
    def test_generate_usage_analytics(self):
        """Test generating usage analytics."""
        # Create some usage logs
        now = timezone.now()
        
        # Log multiple accesses
        for i in range(5):
            CurriculumUsageLog.objects.create(
                facilitator=self.facilitator1,
                curriculum_session=self.curriculum_session1,
                class_section=self.class_section1,
                access_type='view',
                access_timestamp=now - timedelta(hours=i),
                session_duration=300.0  # 5 minutes
            )
        
        for i in range(3):
            CurriculumUsageLog.objects.create(
                facilitator=self.facilitator2,
                curriculum_session=self.curriculum_session2,
                class_section=self.class_section2,
                access_type='view',
                access_timestamp=now - timedelta(hours=i),
                session_duration=240.0  # 4 minutes
            )
        
        # Generate analytics
        metrics = self.service.generate_usage_analytics()
        
        # Verify metrics
        self.assertEqual(metrics.total_accesses, 8)
        self.assertEqual(metrics.unique_facilitators, 2)
        self.assertEqual(metrics.unique_classes, 2)
        self.assertGreater(metrics.average_session_duration, 0)
        self.assertIn(metrics.most_accessed_day, [1, 2])
        self.assertIn(metrics.most_accessed_language, ['english', 'hindi'])
    
    def test_analyze_curriculum_impact(self):
        """Test analyzing curriculum impact."""
        # Create usage logs for curriculum session
        CurriculumUsageLog.objects.create(
            facilitator=self.facilitator1,
            curriculum_session=self.curriculum_session1,
            class_section=self.class_section1,
            access_type='view'
        )
        
        CurriculumUsageLog.objects.create(
            facilitator=self.facilitator2,
            curriculum_session=self.curriculum_session1,
            class_section=self.class_section2,
            access_type='view'
        )
        
        # Analyze impact
        impact = self.service.analyze_curriculum_impact(self.curriculum_session1)
        
        # Verify impact analysis
        self.assertEqual(len(impact.affected_facilitators), 2)
        self.assertEqual(len(impact.affected_classes), 2)
        self.assertEqual(len(impact.notification_recipients), 2)
        
        # Check facilitator data
        facilitator_emails = [f['email'] for f in impact.affected_facilitators]
        self.assertIn('facilitator1@test.com', facilitator_emails)
        self.assertIn('facilitator2@test.com', facilitator_emails)
    
    def test_track_content_effectiveness(self):
        """Test tracking content effectiveness."""
        # Create usage logs
        CurriculumUsageLog.objects.create(
            facilitator=self.facilitator1,
            curriculum_session=self.curriculum_session1,
            class_section=self.class_section1,
            access_type='view',
            session_duration=300.0
        )
        
        CurriculumUsageLog.objects.create(
            facilitator=self.facilitator2,
            curriculum_session=self.curriculum_session1,
            class_section=self.class_section2,
            access_type='view',
            session_duration=240.0
        )
        
        # Track effectiveness
        effectiveness = self.service.track_content_effectiveness(1, 'english')
        
        # Verify effectiveness metrics
        self.assertEqual(effectiveness.day_number, 1)
        self.assertEqual(effectiveness.language, 'english')
        self.assertEqual(effectiveness.access_count, 2)
        self.assertGreater(effectiveness.average_engagement_time, 0)
        self.assertGreaterEqual(effectiveness.completion_rate, 0)
    
    def test_track_content_effectiveness_no_admin_content(self):
        """Test tracking effectiveness when no admin-managed content exists."""
        # Track effectiveness for non-existent content
        effectiveness = self.service.track_content_effectiveness(99, 'english')
        
        # Verify default metrics
        self.assertEqual(effectiveness.day_number, 99)
        self.assertEqual(effectiveness.language, 'english')
        self.assertEqual(effectiveness.access_count, 0)
        self.assertEqual(effectiveness.average_engagement_time, 0.0)
        self.assertIsNone(effectiveness.facilitator_feedback_score)
        self.assertEqual(effectiveness.completion_rate, 0.0)
    
    def test_get_facilitator_usage_summary(self):
        """Test getting facilitator usage summary."""
        # Create usage logs
        now = timezone.now()
        
        for i in range(3):
            CurriculumUsageLog.objects.create(
                facilitator=self.facilitator1,
                curriculum_session=self.curriculum_session1,
                class_section=self.class_section1,
                access_type='view',
                access_timestamp=now - timedelta(hours=i)
            )
        
        # Get summary
        summary = self.service.get_facilitator_usage_summary(self.facilitator1)
        
        # Verify summary
        self.assertEqual(summary['facilitator']['email'], 'facilitator1@test.com')
        self.assertEqual(summary['facilitator']['name'], 'John Doe')
        self.assertEqual(summary['summary']['total_accesses'], 3)
        self.assertEqual(summary['summary']['unique_days_accessed'], 1)
        self.assertEqual(summary['summary']['unique_classes'], 1)
        self.assertEqual(len(summary['recent_activity']), 3)
    
    def test_get_content_popularity_report(self):
        """Test generating content popularity report."""
        # Create usage logs for different content
        now = timezone.now()
        
        # More accesses for curriculum_session1
        for i in range(5):
            CurriculumUsageLog.objects.create(
                facilitator=self.facilitator1,
                curriculum_session=self.curriculum_session1,
                class_section=self.class_section1,
                access_type='view',
                access_timestamp=now - timedelta(hours=i)
            )
        
        # Fewer accesses for curriculum_session2
        for i in range(2):
            CurriculumUsageLog.objects.create(
                facilitator=self.facilitator2,
                curriculum_session=self.curriculum_session2,
                class_section=self.class_section2,
                access_type='view',
                access_timestamp=now - timedelta(hours=i)
            )
        
        # Generate report
        report = self.service.get_content_popularity_report()
        
        # Verify report structure
        self.assertIn('report_period', report)
        self.assertIn('day_popularity', report)
        self.assertIn('language_popularity', report)
        self.assertIn('school_usage', report)
        self.assertIn('summary_stats', report)
        
        # Verify data
        self.assertEqual(report['report_period']['total_accesses'], 7)
        self.assertGreater(len(report['day_popularity']), 0)
        self.assertGreater(len(report['language_popularity']), 0)
    
    def test_error_handling(self):
        """Test error handling in service methods."""
        # Test with invalid facilitator
        with self.assertRaises(Exception):
            self.service.log_curriculum_access(
                facilitator=None,
                curriculum_session=self.curriculum_session1,
                class_section=self.class_section1
            )
        
        # Test with invalid curriculum session
        with self.assertRaises(Exception):
            self.service.analyze_curriculum_impact(None)