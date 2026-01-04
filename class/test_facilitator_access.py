"""
Property-based tests for facilitator access control
**Feature: facilitator-student-management**
"""
import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase as HypothesisTestCase
from .models import User, Role, School, ClassSection, FacilitatorSchool, Student, Enrollment
from .mixins import FacilitatorAccessMixin
from django.views.generic import View
from django.http import HttpResponse


User = get_user_model()


class TestFacilitatorAccessMixin(HypothesisTestCase):
    """Test cases for FacilitatorAccessMixin"""
    
    def setUp(self):
        """Set up test data"""
        # Create roles
        self.admin_role, _ = Role.objects.get_or_create(id=0, defaults={"name": "Admin"})
        self.supervisor_role, _ = Role.objects.get_or_create(id=1, defaults={"name": "Supervisor"})
        self.facilitator_role, _ = Role.objects.get_or_create(id=2, defaults={"name": "Facilitator"})
        
        # Create test view class
        class TestView(FacilitatorAccessMixin, View):
            def get(self, request, *args, **kwargs):
                return HttpResponse("Success")
        
        self.test_view = TestView.as_view()
        self.factory = RequestFactory()
    
    def _create_request_with_user(self, user):
        """Helper to create request with authenticated user"""
        request = self.factory.get('/')
        request.user = user
        
        # Add session and messages middleware
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        
        messages = FallbackStorage(request)
        request._messages = messages
        
        return request
    
    @given(
        facilitator_email=st.emails(),
        school_name=st.text(min_size=1, max_size=100),
        school_udise=st.text(min_size=1, max_size=20),
        school_district=st.text(min_size=1, max_size=50),
        school_block=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_school_assignment_access_control(self, facilitator_email, school_name, school_udise, school_district, school_block):
        """
        **Feature: facilitator-student-management, Property 1: School assignment access control**
        **Validates: Requirements 1.1, 2.5, 3.1, 3.4, 7.1, 7.2**
        
        For any facilitator and any school, the facilitator should only be able to access 
        schools, classes, and students that belong to schools assigned to that facilitator
        """
        # Create facilitator
        facilitator = User.objects.create_user(
            email=facilitator_email,
            password="testpass123",
            role=self.facilitator_role,
            full_name="Test Facilitator"
        )
        
        # Create two schools - one assigned, one not assigned
        assigned_school = School.objects.create(
            name=f"Assigned {school_name}",
            udise=f"A{school_udise}",
            district=school_district,
            block=school_block
        )
        
        unassigned_school = School.objects.create(
            name=f"Unassigned {school_name}",
            udise=f"U{school_udise}",
            district=school_district,
            block=school_block
        )
        
        # Assign facilitator to only one school
        FacilitatorSchool.objects.create(
            facilitator=facilitator,
            school=assigned_school,
            is_active=True
        )
        
        # Create classes in both schools
        assigned_class = ClassSection.objects.create(
            school=assigned_school,
            class_level="1",
            section="A"
        )
        
        unassigned_class = ClassSection.objects.create(
            school=unassigned_school,
            class_level="1",
            section="A"
        )
        
        # Create students in both classes
        assigned_student = Student.objects.create(
            enrollment_number=f"AS{facilitator.id}",
            full_name="Assigned Student",
            gender="M"
        )
        
        unassigned_student = Student.objects.create(
            enrollment_number=f"US{facilitator.id}",
            full_name="Unassigned Student", 
            gender="F"
        )
        
        Enrollment.objects.create(
            student=assigned_student,
            school=assigned_school,
            class_section=assigned_class,
            is_active=True
        )
        
        Enrollment.objects.create(
            student=unassigned_student,
            school=unassigned_school,
            class_section=unassigned_class,
            is_active=True
        )
        
        # Create request with facilitator user
        request = self._create_request_with_user(facilitator)
        
        # Create mixin instance
        mixin = FacilitatorAccessMixin()
        mixin.request = request
        
        # Test school access control
        assert mixin.check_school_access(assigned_school.id) == True, \
            "Facilitator should have access to assigned school"
        assert mixin.check_school_access(unassigned_school.id) == False, \
            "Facilitator should NOT have access to unassigned school"
        
        # Test class access control
        assert mixin.check_class_access(assigned_class.id) == True, \
            "Facilitator should have access to classes in assigned school"
        assert mixin.check_class_access(unassigned_class.id) == False, \
            "Facilitator should NOT have access to classes in unassigned school"
        
        # Test school filtering
        facilitator_schools = mixin.get_facilitator_schools()
        assert assigned_school in facilitator_schools, \
            "Assigned school should be in facilitator's school list"
        assert unassigned_school not in facilitator_schools, \
            "Unassigned school should NOT be in facilitator's school list"
        
        # Test class section filtering
        facilitator_classes = mixin.get_assigned_class_sections()
        assert assigned_class in facilitator_classes, \
            "Classes from assigned school should be accessible"
        assert unassigned_class not in facilitator_classes, \
            "Classes from unassigned school should NOT be accessible"
        
        # Test queryset filtering for enrollments
        all_enrollments = Enrollment.objects.all()
        filtered_enrollments = mixin.filter_by_assigned_schools(all_enrollments)
        
        assigned_enrollment = Enrollment.objects.get(student=assigned_student)
        unassigned_enrollment = Enrollment.objects.get(student=unassigned_student)
        
        assert assigned_enrollment in filtered_enrollments, \
            "Enrollments from assigned schools should be included"
        assert unassigned_enrollment not in filtered_enrollments, \
            "Enrollments from unassigned schools should be filtered out"


class TestFacilitatorAccessEdgeCases(TestCase):
    """Test edge cases for facilitator access control"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_role, _ = Role.objects.get_or_create(id=0, defaults={"name": "Admin"})
        self.facilitator_role, _ = Role.objects.get_or_create(id=2, defaults={"name": "Facilitator"})
        
        self.factory = RequestFactory()
    
    def _create_request_with_user(self, user):
        """Helper to create request with authenticated user"""
        request = self.factory.get('/')
        request.user = user
        
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        
        messages = FallbackStorage(request)
        request._messages = messages
        
        return request
    
    def test_inactive_assignment_access_denied(self):
        """Test that inactive facilitator assignments are properly denied access"""
        facilitator = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=self.facilitator_role,
            full_name="Test Facilitator"
        )
        
        school = School.objects.create(
            name="Test School",
            udise="TEST001",
            district="Test District",
            block="Test Block"
        )
        
        # Create inactive assignment
        FacilitatorSchool.objects.create(
            facilitator=facilitator,
            school=school,
            is_active=False  # Inactive assignment
        )
        
        request = self._create_request_with_user(facilitator)
        mixin = FacilitatorAccessMixin()
        mixin.request = request
        
        # Should not have access to school with inactive assignment
        assert mixin.check_school_access(school.id) == False, \
            "Facilitator should NOT have access to school with inactive assignment"
    
    def test_nonexistent_school_access_denied(self):
        """Test that access to non-existent schools is properly denied"""
        facilitator = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=self.facilitator_role,
            full_name="Test Facilitator"
        )
        
        request = self._create_request_with_user(facilitator)
        mixin = FacilitatorAccessMixin()
        mixin.request = request
        
        # Should not have access to non-existent school
        nonexistent_school_id = 99999
        assert mixin.check_school_access(nonexistent_school_id) == False, \
            "Facilitator should NOT have access to non-existent school"
    
    def test_nonexistent_class_access_denied(self):
        """Test that access to non-existent classes is properly denied"""
        facilitator = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=self.facilitator_role,
            full_name="Test Facilitator"
        )
        
        request = self._create_request_with_user(facilitator)
        mixin = FacilitatorAccessMixin()
        mixin.request = request
        
        # Should not have access to non-existent class
        nonexistent_class_id = 99999
        assert mixin.check_class_access(nonexistent_class_id) == False, \
            "Facilitator should NOT have access to non-existent class"