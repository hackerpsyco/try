"""
Tests for SessionIntegrationService.
"""

import pytest
from django.test import TestCase
from django.utils import timezone
from unittest.mock import Mock

from ..models import (
    CurriculumSession, User, Role, School, ClassSection, 
    PlannedSession, SessionContentMapping, CurriculumUsageLog, CurriculumStatus
)
from .session_integration_service import SessionIntegrationService, IntegratedSessionData, AlignmentReport


class TestSessionIntegrationService(TestCase):
    """Test cases for SessionIntegrationService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = SessionIntegrationService()
        
        # Create admin role
        self.admin_role, _ = Role.objects.get_or_create(
            id=0,
            defaults={'name': 'Admin'}
        )
        
        # Create facilitator role
        self.facilitator_role, _ = Role.objects.get_or_create(
            id=2,
            defaults={'name': 'Facilitator'}
        )
        
        # Create test users
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role=self.admin_role,
            full_name='Test Admin'
        )
        
        self.facilitator_user = User.objects.create_user(
            email='facilitator@test.com',
            password='testpass123',
            role=self.facilitator_role,
            full_name='Test Facilitator'
        )
        
        # Create test school
        self.school = School.objects.create(
            name='Test School',
            udise='TEST001',
            block='Test Block',
            district='Test District',
            enrolled_students=100
        )
        
        # Create test class section
        self.class_section = ClassSection.objects.create(
            school=self.school,
            class_level='5',
            section='A'
        )
        
        # Create test curriculum session
        self.curriculum_session = CurriculumSession.objects.create(
            title='Test Curriculum Day 1',
            day_number=1,
            language='english',
            content='<p>Test curriculum content</p>',
            learning_objectives='Test learning objectives',
            status=CurriculumStatus.PUBLISHED,
            created_by=self.admin_user,
            is_active_for_facilitators=True
        )
        
        # Get the auto-generated planned session for day 1 (created by the system)
        self.planned_session = PlannedSession.objects.get(
            class_section=self.class_section,
            day_number=1
        )
    
    def test_link_planned_to_curriculum_success(self):
        """Test successful linking of planned session to curriculum session."""
        result = self.service.link_planned_to_curriculum(self.planned_session)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, self.curriculum_session.id)
        
        # Check that mapping was created
        mapping = SessionContentMapping.objects.get(planned_session=self.planned_session)
        self.assertEqual(mapping.curriculum_session, self.curriculum_session)
        self.assertEqual(mapping.content_source, 'admin_managed')
        self.assertEqual(mapping.sync_status, 'synced')
    
    def test_link_planned_to_curriculum_no_match(self):
        """Test linking when no matching curriculum session exists."""
        # Create planned session for day that has no curriculum session
        planned_session_no_match = PlannedSession.objects.create(
            class_section=self.class_section,
            day_number=99,
            title='Test Planned Session Day 99'
        )
        
        result = self.service.link_planned_to_curriculum(planned_session_no_match)
        
        self.assertIsNone(result)
        
        # Check that mapping was created with static fallback
        mapping = SessionContentMapping.objects.get(planned_session=planned_session_no_match)
        self.assertIsNone(mapping.curriculum_session)
        self.assertEqual(mapping.content_source, 'static_fallback')
    
    def test_get_integrated_session_data_with_curriculum(self):
        """Test getting integrated data when curriculum session exists."""
        # First link the sessions
        self.service.link_planned_to_curriculum(self.planned_session)
        
        result = self.service.get_integrated_session_data(self.planned_session)
        
        self.assertIsInstance(result, IntegratedSessionData)
        self.assertEqual(result.planned_session, self.planned_session)
        self.assertEqual(result.curriculum_session, self.curriculum_session)
        self.assertEqual(result.content_source, 'admin_managed')
        self.assertTrue(result.has_admin_content)
        self.assertIn('Test Curriculum Day 1', result.curriculum_content)
    
    def test_get_integrated_session_data_without_curriculum(self):
        """Test getting integrated data when no curriculum session exists."""
        # Create planned session without matching curriculum
        planned_session_no_match = PlannedSession.objects.create(
            class_section=self.class_section,
            day_number=99,
            title='Test Planned Session Day 99'
        )
        
        result = self.service.get_integrated_session_data(planned_session_no_match)
        
        self.assertIsInstance(result, IntegratedSessionData)
        self.assertEqual(result.planned_session, planned_session_no_match)
        self.assertIsNone(result.curriculum_session)
        self.assertEqual(result.content_source, 'static_fallback')
        self.assertFalse(result.has_admin_content)
        self.assertEqual(result.curriculum_content, '')
    
    def test_update_session_relationships(self):
        """Test updating session relationships when curriculum session changes."""
        # Create additional planned sessions for the same day
        planned_session_2 = PlannedSession.objects.create(
            class_section=self.class_section,
            day_number=1,
            title='Another Planned Session Day 1'
        )
        
        # Create another class section
        class_section_2 = ClassSection.objects.create(
            school=self.school,
            class_level='6',
            section='A'
        )
        
        planned_session_3 = PlannedSession.objects.create(
            class_section=class_section_2,
            day_number=1,
            title='Third Planned Session Day 1'
        )
        
        affected_sessions = self.service.update_session_relationships(self.curriculum_session)
        
        # Should affect all planned sessions with matching day and language
        self.assertEqual(len(affected_sessions), 3)
        
        # Check that all mappings were created/updated
        for planned_session in [self.planned_session, planned_session_2, planned_session_3]:
            mapping = SessionContentMapping.objects.get(planned_session=planned_session)
            self.assertEqual(mapping.curriculum_session, self.curriculum_session)
            self.assertEqual(mapping.content_source, 'admin_managed')
    
    def test_validate_session_alignment_good(self):
        """Test alignment validation with good alignment."""
        # Create curriculum sessions for multiple days
        for day in range(1, 4):
            CurriculumSession.objects.create(
                title=f'Test Curriculum Day {day}',
                day_number=day,
                language='english',
                content=f'<p>Test content for day {day}</p>',
                status=CurriculumStatus.PUBLISHED,
                created_by=self.admin_user,
                is_active_for_facilitators=True
            )
        
        # Create planned sessions for the same days
        for day in range(1, 4):
            if day != 1:  # Day 1 already exists
                PlannedSession.objects.create(
                    class_section=self.class_section,
                    day_number=day,
                    title=f'Test Planned Session Day {day}'
                )
        
        report = self.service.validate_session_alignment(self.class_section)
        
        self.assertIsInstance(report, AlignmentReport)
        self.assertEqual(report.class_section, self.class_section)
        self.assertEqual(report.total_planned_sessions, 3)
        self.assertEqual(report.sessions_with_curriculum, 3)
        self.assertEqual(report.sessions_without_curriculum, 0)
        self.assertEqual(report.alignment_percentage, 100.0)
        self.assertEqual(len(report.misaligned_sessions), 0)
    
    def test_validate_session_alignment_poor(self):
        """Test alignment validation with poor alignment."""
        # Create planned sessions without matching curriculum sessions
        for day in range(2, 6):
            PlannedSession.objects.create(
                class_section=self.class_section,
                day_number=day,
                title=f'Test Planned Session Day {day}'
            )
        
        report = self.service.validate_session_alignment(self.class_section)
        
        self.assertEqual(report.total_planned_sessions, 5)  # Days 1-5
        self.assertEqual(report.sessions_with_curriculum, 1)  # Only day 1 has curriculum
        self.assertEqual(report.sessions_without_curriculum, 4)  # Days 2-5 don't
        self.assertEqual(report.alignment_percentage, 20.0)
        self.assertEqual(len(report.misaligned_sessions), 4)
    
    def test_bulk_link_sessions(self):
        """Test bulk linking of sessions."""
        # Create additional planned sessions
        for day in range(2, 6):
            PlannedSession.objects.create(
                class_section=self.class_section,
                day_number=day,
                title=f'Test Planned Session Day {day}'
            )
        
        # Create curriculum session for day 2
        CurriculumSession.objects.create(
            title='Test Curriculum Day 2',
            day_number=2,
            language='english',
            content='<p>Test content for day 2</p>',
            status=CurriculumStatus.PUBLISHED,
            created_by=self.admin_user,
            is_active_for_facilitators=True
        )
        
        stats = self.service.bulk_link_sessions(self.class_section)
        
        self.assertEqual(stats['total_sessions'], 5)
        self.assertEqual(stats['linked_to_admin'], 2)  # Days 1 and 2
        self.assertEqual(stats['linked_to_static'], 3)  # Days 3, 4, 5
        self.assertEqual(stats['errors'], 0)
    
    def test_log_curriculum_access(self):
        """Test logging curriculum access."""
        # First link the sessions
        self.service.link_planned_to_curriculum(self.planned_session)
        
        # Mock request object
        mock_request = Mock()
        mock_request.META = {
            'HTTP_USER_AGENT': 'Test Browser',
            'REMOTE_ADDR': '127.0.0.1'
        }
        
        usage_log = self.service.log_curriculum_access(
            self.planned_session, 
            self.facilitator_user, 
            mock_request
        )
        
        self.assertIsNotNone(usage_log)
        self.assertEqual(usage_log.curriculum_session, self.curriculum_session)
        self.assertEqual(usage_log.facilitator, self.facilitator_user)
        self.assertEqual(usage_log.class_section, self.class_section)
        self.assertEqual(usage_log.planned_session, self.planned_session)
        self.assertEqual(usage_log.content_source, 'admin_managed')
        self.assertEqual(usage_log.user_agent, 'Test Browser')
        self.assertEqual(usage_log.ip_address, '127.0.0.1')
    
    def test_get_class_language(self):
        """Test getting class language."""
        language = self.service._get_class_language(self.class_section)
        self.assertEqual(language, 'english')
        
        # Test with class section without language (should default to english)
        class_section_no_lang = ClassSection.objects.create(
            school=self.school,
            class_level='4',
            section='B'
        )
        
        language = self.service._get_class_language(class_section_no_lang)
        self.assertEqual(language, 'english')
    
    def test_find_curriculum_session(self):
        """Test finding curriculum session."""
        result = self.service._find_curriculum_session(1, 'english')
        self.assertEqual(result, self.curriculum_session)
        
        # Test with non-existent session
        result = self.service._find_curriculum_session(99, 'english')
        self.assertIsNone(result)
    
    def test_get_or_create_mapping(self):
        """Test getting or creating session content mapping."""
        mapping = self.service._get_or_create_mapping(self.planned_session)
        
        self.assertIsInstance(mapping, SessionContentMapping)
        self.assertEqual(mapping.planned_session, self.planned_session)
        
        # Test that it returns the same mapping on second call
        mapping2 = self.service._get_or_create_mapping(self.planned_session)
        self.assertEqual(mapping.id, mapping2.id)
    
    def test_load_curriculum_content(self):
        """Test loading curriculum content."""
        content = self.service._load_curriculum_content(self.curriculum_session)
        
        self.assertIn('Test Curriculum Day 1', content)
        self.assertIn('Test learning objectives', content)
        self.assertIn('<p>Test curriculum content</p>', content)
    
    def test_generate_alignment_recommendations(self):
        """Test generating alignment recommendations."""
        # Test low alignment
        recommendations = self.service._generate_alignment_recommendations(30.0, 7, 'english')
        self.assertTrue(any('Low alignment' in rec for rec in recommendations))
        self.assertTrue(any('Create 7 curriculum sessions' in rec for rec in recommendations))
        
        # Test good alignment
        recommendations = self.service._generate_alignment_recommendations(85.0, 2, 'hindi')
        self.assertTrue(any('Good alignment' in rec for rec in recommendations))
        self.assertTrue(any('Create 2 curriculum sessions' in rec for rec in recommendations))
