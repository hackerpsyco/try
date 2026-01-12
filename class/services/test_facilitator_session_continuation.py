"""
Tests for Facilitator Session Continuation Service
"""

import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

# Import models using relative imports to avoid 'class' keyword issue
from ..models import School, ClassSection, PlannedSession, ActualSession, Student, Enrollment, Attendance, SessionStatus
from .facilitator_session_continuation import (
    FacilitatorAssignmentHistory, FacilitatorSessionContinuation
)

User = get_user_model()


@pytest.mark.django_db
class TestFacilitatorSessionContinuation(TestCase):
    """Test facilitator session continuation logic"""
    
    def setUp(self):
        """Set up test data"""
        # Create school
        self.school = School.objects.create(
            name="Test School",
            udise="TS001",
            block="Test Block",
            district="Test District"
        )
        
        # Create class section
        self.class_section = ClassSection.objects.create(
            school=self.school,
            class_level="1",
            section="A",
            academic_year="2024-2025"
        )
        
        # Create facilitators
        # First create the facilitator role
        from ..models import Role
        facilitator_role, _ = Role.objects.get_or_create(
            id=2,
            defaults={"name": "Facilitator"}
        )
        
        self.facilitator1 = User.objects.create_user(
            email="facilitator1@test.com",
            password="testpass123",
            full_name="Facilitator One",
            role=facilitator_role
        )
        
        self.facilitator2 = User.objects.create_user(
            email="facilitator2@test.com",
            password="testpass123",
            full_name="Facilitator Two",
            role=facilitator_role
        )
        
        # Get auto-generated planned sessions (system creates 150 on class creation)
        self.planned_sessions = list(
            PlannedSession.objects.filter(
                class_section=self.class_section,
                is_active=True
            ).order_by('day_number')
        )
    
    def test_get_continuation_day_no_sessions(self):
        """Test continuation day when no sessions have been conducted"""
        history = FacilitatorAssignmentHistory(self.class_section)
        continuation_day = history.get_continuation_day()
        
        # Should start from day 1
        assert continuation_day == 1
    
    def test_get_continuation_day_after_50_sessions(self):
        """Test continuation day after 50 sessions completed"""
        # Conduct first 50 sessions with facilitator1
        today = timezone.now().date()
        for day in range(1, 51):
            ActualSession.objects.create(
                planned_session=self.planned_sessions[day - 1],
                date=today,
                facilitator=self.facilitator1,
                status=SessionStatus.CONDUCTED
            )
        
        history = FacilitatorAssignmentHistory(self.class_section)
        continuation_day = history.get_continuation_day()
        
        # Should continue from day 51
        assert continuation_day == 51
    
    def test_get_next_session_for_new_facilitator(self):
        """Test that new facilitator gets continuation day, not day 1"""
        # Conduct first 50 sessions with facilitator1
        today = timezone.now().date()
        for day in range(1, 51):
            ActualSession.objects.create(
                planned_session=self.planned_sessions[day - 1],
                date=today,
                facilitator=self.facilitator1,
                status=SessionStatus.CONDUCTED
            )
        
        # Get next session for facilitator2 (new to this class)
        next_session = FacilitatorSessionContinuation.get_next_session_for_facilitator(
            self.class_section, self.facilitator2
        )
        
        # Should be day 51, not day 1
        assert next_session is not None
        assert next_session.day_number == 51
    
    def test_get_next_session_for_existing_facilitator(self):
        """Test that existing facilitator gets next pending session"""
        # Conduct first 50 sessions with facilitator1
        today = timezone.now().date()
        for day in range(1, 51):
            ActualSession.objects.create(
                planned_session=self.planned_sessions[day - 1],
                date=today,
                facilitator=self.facilitator1,
                status=SessionStatus.CONDUCTED
            )
        
        # Get next session for facilitator1 (already worked on this class)
        next_session = FacilitatorSessionContinuation.get_next_session_for_facilitator(
            self.class_section, self.facilitator1
        )
        
        # Should be day 51 (next pending)
        assert next_session is not None
        assert next_session.day_number == 51
    
    def test_facilitator_assignment_history(self):
        """Test facilitator assignment history tracking"""
        today = timezone.now().date()
        
        # Facilitator1 conducts days 1-50
        for day in range(1, 51):
            ActualSession.objects.create(
                planned_session=self.planned_sessions[day - 1],
                date=today,
                facilitator=self.facilitator1,
                status=SessionStatus.CONDUCTED
            )
        
        # Facilitator2 conducts days 51-100
        for day in range(51, 101):
            ActualSession.objects.create(
                planned_session=self.planned_sessions[day - 1],
                date=today,
                facilitator=self.facilitator2,
                status=SessionStatus.CONDUCTED
            )
        
        history = FacilitatorAssignmentHistory(self.class_section)
        assignments = history.get_assignment_summary()
        
        # Should have 2 assignments
        assert len(assignments) == 2
        
        # First assignment: facilitator1, days 1-50
        assert assignments[0]['facilitator'] == self.facilitator1
        assert assignments[0]['start_day'] == 1
        assert assignments[0]['end_day'] == 50
        assert assignments[0]['total_days'] == 50
        
        # Second assignment: facilitator2, days 51-100
        assert assignments[1]['facilitator'] == self.facilitator2
        assert assignments[1]['start_day'] == 51
        assert assignments[1]['end_day'] == 100
        assert assignments[1]['total_days'] == 50
    
    def test_assign_facilitator_to_class(self):
        """Test facilitator assignment with continuation logic"""
        today = timezone.now().date()
        
        # Conduct first 50 sessions with facilitator1
        for day in range(1, 51):
            ActualSession.objects.create(
                planned_session=self.planned_sessions[day - 1],
                date=today,
                facilitator=self.facilitator1,
                status=SessionStatus.CONDUCTED
            )
        
        # Assign facilitator2
        result = FacilitatorSessionContinuation.assign_facilitator_to_class(
            self.class_section, self.facilitator2
        )
        
        # Verify assignment result
        assert result['success'] is True
        assert result['last_completed_day'] == 50
        assert result['continuation_day'] == 51
        assert result['previous_facilitator'] == self.facilitator1.full_name
        assert result['next_session']['day_number'] == 51
    
    def test_validate_facilitator_transition(self):
        """Test validation of facilitator transition"""
        today = timezone.now().date()
        
        # Conduct first 50 sessions with facilitator1
        for day in range(1, 51):
            ActualSession.objects.create(
                planned_session=self.planned_sessions[day - 1],
                date=today,
                facilitator=self.facilitator1,
                status=SessionStatus.CONDUCTED
            )
        
        # Validate transition from facilitator1 to facilitator2
        result = FacilitatorSessionContinuation.validate_facilitator_transition(
            self.class_section, self.facilitator1, self.facilitator2
        )
        
        # Should be valid
        assert result['is_valid'] is True
        assert result['transition_details']['old_facilitator'] == self.facilitator1.full_name
        assert result['transition_details']['new_facilitator'] == self.facilitator2.full_name
        assert result['transition_details']['last_completed_day'] == 50
        assert result['transition_details']['continuation_day'] == 51
    
    def test_get_facilitator_workload(self):
        """Test facilitator workload calculation"""
        today = timezone.now().date()
        
        # Facilitator1 conducts days 1-50
        for day in range(1, 51):
            ActualSession.objects.create(
                planned_session=self.planned_sessions[day - 1],
                date=today,
                facilitator=self.facilitator1,
                status=SessionStatus.CONDUCTED
            )
        
        workload = FacilitatorSessionContinuation.get_facilitator_workload(self.facilitator1)
        
        # Verify workload
        assert workload['facilitator'] == self.facilitator1.full_name
        assert workload['total_classes'] == 1
        assert workload['total_days_conducted'] == 50
        assert len(workload['classes']) == 1
        assert workload['classes'][0]['days_conducted'] == 50
        assert workload['classes'][0]['last_day_worked'] == 50
    
    def test_get_class_facilitator_timeline(self):
        """Test facilitator timeline for a class"""
        today = timezone.now().date()
        
        # Facilitator1 conducts days 1-50
        for day in range(1, 51):
            ActualSession.objects.create(
                planned_session=self.planned_sessions[day - 1],
                date=today,
                facilitator=self.facilitator1,
                status=SessionStatus.CONDUCTED
            )
        
        # Facilitator2 conducts days 51-100
        for day in range(51, 101):
            ActualSession.objects.create(
                planned_session=self.planned_sessions[day - 1],
                date=today,
                facilitator=self.facilitator2,
                status=SessionStatus.CONDUCTED
            )
        
        timeline = FacilitatorSessionContinuation.get_class_facilitator_timeline(self.class_section)
        
        # Should have 2 entries
        assert len(timeline) == 2
        
        # First entry
        assert timeline[0]['facilitator'] == self.facilitator1.full_name
        assert timeline[0]['start_day'] == 1
        assert timeline[0]['end_day'] == 50
        assert timeline[0]['total_days'] == 50
        assert timeline[0]['percentage'] == 33.33
        
        # Second entry
        assert timeline[1]['facilitator'] == self.facilitator2.full_name
        assert timeline[1]['start_day'] == 51
        assert timeline[1]['end_day'] == 100
        assert timeline[1]['total_days'] == 50
        assert timeline[1]['percentage'] == 33.33
    
    def test_continuation_with_cancelled_sessions(self):
        """Test continuation day calculation with cancelled sessions"""
        today = timezone.now().date()
        
        # Conduct days 1-40
        for day in range(1, 41):
            ActualSession.objects.create(
                planned_session=self.planned_sessions[day - 1],
                date=today,
                facilitator=self.facilitator1,
                status=SessionStatus.CONDUCTED
            )
        
        # Cancel days 41-50
        for day in range(41, 51):
            ActualSession.objects.create(
                planned_session=self.planned_sessions[day - 1],
                date=today,
                facilitator=self.facilitator1,
                status=SessionStatus.CANCELLED,
                cancellation_reason='emergency'
            )
        
        history = FacilitatorAssignmentHistory(self.class_section)
        continuation_day = history.get_continuation_day()
        
        # Should continue from day 51 (after last completed/cancelled)
        assert continuation_day == 51
    
    def test_continuation_with_holiday_sessions(self):
        """Test that holiday sessions don't block continuation"""
        today = timezone.now().date()
        
        # Conduct days 1-40
        for day in range(1, 41):
            ActualSession.objects.create(
                planned_session=self.planned_sessions[day - 1],
                date=today,
                facilitator=self.facilitator1,
                status=SessionStatus.CONDUCTED
            )
        
        # Mark days 41-50 as holiday
        for day in range(41, 51):
            ActualSession.objects.create(
                planned_session=self.planned_sessions[day - 1],
                date=today,
                facilitator=self.facilitator1,
                status=SessionStatus.HOLIDAY
            )
        
        # Get next session for facilitator2
        next_session = FacilitatorSessionContinuation.get_next_session_for_facilitator(
            self.class_section, self.facilitator2
        )
        
        # Should be day 41 (first pending, not day 51)
        # Because holiday sessions are still pending
        assert next_session is not None
        assert next_session.day_number == 41
