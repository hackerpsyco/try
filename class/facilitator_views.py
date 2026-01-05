"""
Facilitator Student Management Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from .models import School, ClassSection, Student, Enrollment, FacilitatorSchool, User
from .mixins import FacilitatorAccessMixin
from .decorators import facilitator_required
from .forms import AddUserForm  # We'll need to create a student form
import logging
from datetime import date
logger = logging.getLogger(__name__)


class FacilitatorSchoolListView(FacilitatorAccessMixin, ListView):
    """
    View for facilitators to see their assigned schools
    """
    model = School
    template_name = 'facilitator/schools/list.html'
    context_object_name = 'schools'
    
    def get_queryset(self):
        """Return only schools assigned to the current facilitator, ordered alphabetically"""
        return self.get_facilitator_schools().order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add enrollment counts for each school
        schools_with_counts = []
        for school in context['schools']:
            enrollment_count = Enrollment.objects.filter(
                school=school,
                is_active=True
            ).count()
            
            class_count = ClassSection.objects.filter(
                school=school,
                is_active=True
            ).count()
            
            schools_with_counts.append({
                'school': school,
                'enrollment_count': enrollment_count,
                'class_count': class_count
            })
        
        context['schools_with_counts'] = schools_with_counts
        return context


class FacilitatorSchoolDetailView(FacilitatorAccessMixin, DetailView):
    """
    View for facilitators to see classes within their assigned school
    """
    model = School
    template_name = 'facilitator/schools/detail.html'
    context_object_name = 'school'
    
    def get_object(self, queryset=None):
        """Get school and verify facilitator has access"""
        school = super().get_object(queryset)
        self.verify_school_access_or_403(school.id)
        return school
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        school = self.object
        
        # Get all classes for this school
        classes = ClassSection.objects.filter(
            school=school,
            is_active=True
        ).order_by('class_level', 'section')
        
        # Add enrollment counts for each class
        classes_with_counts = []
        for class_section in classes:
            enrollment_count = Enrollment.objects.filter(
                class_section=class_section,
                is_active=True
            ).count()
            
            classes_with_counts.append({
                'class_section': class_section,
                'enrollment_count': enrollment_count
            })
        
        context['classes_with_counts'] = classes_with_counts
        
        # Add filtering options
        grade_levels = classes.values_list('class_level', flat=True).distinct()
        context['grade_levels'] = sorted(set(grade_levels))
        
        # Apply filters if provided
        grade_filter = self.request.GET.get('grade')
        if grade_filter:
            classes_with_counts = [
                item for item in classes_with_counts 
                if item['class_section'].class_level == grade_filter
            ]
            context['selected_grade'] = grade_filter
        
        context['filtered_classes'] = classes_with_counts
        return context


class FacilitatorStudentListView(FacilitatorAccessMixin, ListView):
    """
    View for facilitators to see students from their assigned schools
    """
    model = Enrollment
    template_name = 'facilitator/students/list.html'
    context_object_name = 'enrollments'
    paginate_by = 20
    
    def get_queryset(self):
        """Return students from facilitator's assigned schools"""
        queryset = Enrollment.objects.filter(
            is_active=True,
            school__in=self.get_facilitator_schools()
        ).select_related('student', 'class_section', 'school').order_by('student__full_name')
        
        # Apply filters
        school_filter = self.request.GET.get('school')
        class_filter = self.request.GET.get('class')
        grade_filter = self.request.GET.get('grade')
        search_query = self.request.GET.get('search')
        
        if school_filter:
            queryset = queryset.filter(school_id=school_filter)
        
        if class_filter:
            queryset = queryset.filter(class_section_id=class_filter)
        
        if grade_filter:
            queryset = queryset.filter(class_section__class_level=grade_filter)
        
        if search_query:
            queryset = queryset.filter(
                Q(student__full_name__icontains=search_query) |
                Q(student__enrollment_number__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        context['schools'] = self.get_facilitator_schools()
        
        # Get classes from assigned schools
        context['classes'] = self.get_assigned_class_sections()
        
        # Get unique grade levels
        grade_levels = ClassSection.objects.filter(
            school__in=self.get_facilitator_schools()
        ).values_list('class_level', flat=True).distinct()
        context['grade_levels'] = sorted(set(grade_levels))
        
        # Preserve filter values
        context['filters'] = {
            'school': self.request.GET.get('school', ''),
            'class': self.request.GET.get('class', ''),
            'grade': self.request.GET.get('grade', ''),
            'search': self.request.GET.get('search', ''),
        }
        
        # Calculate attendance statistics for each enrollment
        from .models import Attendance, ActualSession
        enrollment_stats = []
        
        for enrollment in context['enrollments']:
            # Get total conducted sessions for this class
            total_sessions = ActualSession.objects.filter(
                planned_session__class_section=enrollment.class_section,
                status="conducted"
            ).count()
            
            # Count attendance records for this student
            present_count = Attendance.objects.filter(
                enrollment=enrollment,
                actual_session__planned_session__class_section=enrollment.class_section,
                status="present"
            ).count()
            
            absent_count = Attendance.objects.filter(
                enrollment=enrollment,
                actual_session__planned_session__class_section=enrollment.class_section,
                status="absent"
            ).count()
            
            attendance_percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0
            
            enrollment_stats.append({
                'enrollment': enrollment,
                'total_sessions': total_sessions,
                'present_count': present_count,
                'absent_count': absent_count,
                'attendance_percentage': round(attendance_percentage, 1)
            })
        
        context['enrollment_stats'] = enrollment_stats
        
        return context


class FacilitatorStudentCreateView(FacilitatorAccessMixin, CreateView):
    """
    View for facilitators to create new students
    """
    model = Student
    template_name = 'facilitator/students/create.html'
    fields = ['enrollment_number', 'full_name', 'gender']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Only show classes from facilitator's assigned schools
        context['class_sections'] = self.get_assigned_class_sections()
        context['schools'] = self.get_facilitator_schools()
        
        return context
    
    def form_valid(self, form):
        """Create student and enrollment"""
        # Get the selected class section
        class_section_id = self.request.POST.get('class_section')
        if not class_section_id:
            messages.error(self.request, "Please select a class section.")
            return self.form_invalid(form)
        
        # Verify facilitator has access to this class
        self.verify_class_access_or_403(class_section_id)
        
        class_section = get_object_or_404(ClassSection, id=class_section_id)
        
        # Save the student
        student = form.save()
        
        # Create enrollment with start_date
        Enrollment.objects.create(
            student=student,
            school=class_section.school,
            class_section=class_section,
            start_date=date.today(),  # Add current date as start_date
            is_active=True
        )
        
        messages.success(self.request, f"Student {student.full_name} created successfully!")
        return redirect('facilitator_students_list')


class FacilitatorStudentUpdateView(FacilitatorAccessMixin, UpdateView):
    """
    View for facilitators to edit existing students
    """
    model = Student
    template_name = 'facilitator/students/edit.html'
    fields = ['enrollment_number', 'full_name', 'gender']
    
    def get_object(self, queryset=None):
        """Get student and verify facilitator has access"""
        student = super().get_object(queryset)
        
        # Check if student is enrolled in any of facilitator's schools
        enrollment = Enrollment.objects.filter(
            student=student,
            is_active=True,
            school__in=self.get_facilitator_schools()
        ).first()
        
        if not enrollment:
            raise PermissionDenied("You do not have access to this student.")
        
        return student
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current enrollment
        student = self.object
        current_enrollment = Enrollment.objects.filter(
            student=student,
            is_active=True,
            school__in=self.get_facilitator_schools()
        ).first()
        
        context['current_enrollment'] = current_enrollment
        context['class_sections'] = self.get_assigned_class_sections()
        context['schools'] = self.get_facilitator_schools()
        
        return context
    
    def form_valid(self, form):
        """Update student and enrollment if class changed"""
        student = form.save()
        
        # Check if class section was changed
        new_class_section_id = self.request.POST.get('class_section')
        if new_class_section_id:
            # Verify facilitator has access to new class
            self.verify_class_access_or_403(new_class_section_id)
            
            new_class_section = get_object_or_404(ClassSection, id=new_class_section_id)
            
            # Update enrollment
            current_enrollment = Enrollment.objects.filter(
                student=student,
                is_active=True,
                school__in=self.get_facilitator_schools()
            ).first()
            
            if current_enrollment:
                current_enrollment.class_section = new_class_section
                current_enrollment.school = new_class_section.school
                current_enrollment.save()
        
        messages.success(self.request, f"Student {student.full_name} updated successfully!")
        return redirect('facilitator_students_list')


# Function-based views for AJAX endpoints
@facilitator_required
def facilitator_ajax_school_classes(request):
    """AJAX endpoint to get classes for a specific school - Simplified version"""
    school_id = request.GET.get('school_id')
    
    if not school_id:
        return JsonResponse({'error': 'School ID required'}, status=400)
    
    try:
        # Check if facilitator has access to this school
        facilitator_schools = FacilitatorSchool.objects.filter(
            facilitator=request.user,
            school_id=school_id,
            is_active=True
        ).exists()
        
        if not facilitator_schools:
            return JsonResponse({'error': 'Access denied - School not assigned to facilitator'}, status=403)
        
        # Get classes for the school
        classes = ClassSection.objects.filter(
            school_id=school_id,
            is_active=True
        ).order_by('class_level', 'section')
        
        # Convert to simple list
        classes_data = []
        for cls in classes:
            classes_data.append({
                'id': str(cls.id),
                'class_level': cls.class_level,
                'section': cls.section or '',
                'display_name': cls.display_name or f"{cls.class_level}{cls.section or ''}"
            })
        
        return JsonResponse({
            'success': True,
            'classes': classes_data,
            'count': len(classes_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


@facilitator_required
def facilitator_student_detail(request, student_id):
    """View student details and attendance"""
    student = get_object_or_404(Student, id=student_id)
    
    # Create mixin instance to check access
    mixin = FacilitatorAccessMixin()
    mixin.request = request
    
    # Check if student is in facilitator's schools
    enrollment = Enrollment.objects.filter(
        student=student,
        is_active=True,
        school__in=mixin.get_facilitator_schools()
    ).first()
    
    if not enrollment:
        messages.error(request, "You do not have access to this student.")
        return redirect('facilitator_students_list')
    
    # Get attendance statistics
    from .models import Attendance, ActualSession
    
    total_sessions = ActualSession.objects.filter(
        planned_session__class_section=enrollment.class_section,
        status='conducted'
    ).count()
    
    present_count = Attendance.objects.filter(
        enrollment=enrollment,
        status='present'
    ).count()
    
    absent_count = Attendance.objects.filter(
        enrollment=enrollment,
        status='absent'
    ).count()
    
    attendance_percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0
    
    # Get recent attendance records
    recent_attendance = Attendance.objects.filter(
        enrollment=enrollment
    ).select_related('actual_session__planned_session').order_by('-actual_session__date')[:10]
    
    context = {
        'student': student,
        'enrollment': enrollment,
        'stats': {
            'total_sessions': total_sessions,
            'present_count': present_count,
            'absent_count': absent_count,
            'attendance_percentage': round(attendance_percentage, 1)
        },
        'recent_attendance': recent_attendance
    }
    
    return render(request, 'facilitator/students/detail.html', context)


@facilitator_required
def facilitator_debug_schools(request):
    """Debug view to check facilitator school access"""
    mixin = FacilitatorAccessMixin()
    mixin.request = request
    
    schools = mixin.get_facilitator_schools()
    school_data = []
    
    for school in schools:
        classes = ClassSection.objects.filter(school=school, is_active=True)
        school_data.append({
            'school': school,
            'classes': classes,
            'class_count': classes.count()
        })
    
    return JsonResponse({
        'facilitator_id': str(request.user.id),
        'facilitator_name': request.user.full_name,
        'schools_count': schools.count(),
        'schools': [
            {
                'id': str(item['school'].id),
                'name': item['school'].name,
                'class_count': item['class_count'],
                'classes': [
                    {
                        'id': str(cls.id),
                        'display_name': cls.display_name,
                        'class_level': cls.class_level,
                        'section': cls.section
                    } for cls in item['classes']
                ]
            } for item in school_data
        ]
    })

@facilitator_required
def facilitator_test_access(request):
    """Test view to check facilitator access and data"""
    from django.http import HttpResponse
    
    mixin = FacilitatorAccessMixin()
    mixin.request = request
    
    # Get facilitator schools
    schools = mixin.get_facilitator_schools()
    
    html = f"""
    <html>
    <head><title>Facilitator Access Test</title></head>
    <body>
        <h1>Facilitator Access Test</h1>
        <p><strong>User:</strong> {request.user.full_name} (ID: {request.user.id})</p>
        <p><strong>Role:</strong> {request.user.role.name}</p>
        <p><strong>Schools Assigned:</strong> {schools.count()}</p>
        
        <h2>Schools and Classes:</h2>
    """
    
    if schools.count() == 0:
        html += "<p style='color: red;'>No schools assigned to this facilitator!</p>"
        html += "<p>Please contact admin to assign schools to this facilitator.</p>"
    else:
        for school in schools:
            classes = ClassSection.objects.filter(school=school, is_active=True)
            html += f"""
            <div style='border: 1px solid #ccc; margin: 10px; padding: 10px;'>
                <h3>{school.name} (ID: {school.id})</h3>
                <p>Classes: {classes.count()}</p>
                <ul>
            """
            
            for cls in classes:
                html += f"<li>{cls.display_name} (ID: {cls.id})</li>"
            
            html += "</ul></div>"
    
    html += """
        <h2>Test AJAX Endpoint:</h2>
        <p>Select a school to test the AJAX endpoint:</p>
        <select id="schoolSelect" onchange="testAjax()">
            <option value="">Select School</option>
    """
    
    for school in schools:
        html += f'<option value="{school.id}">{school.name}</option>'
    
    html += """
        </select>
        <div id="result" style="margin-top: 20px; padding: 10px; border: 1px solid #ddd;"></div>
        
        <script>
        function testAjax() {
            const schoolId = document.getElementById('schoolSelect').value;
            const resultDiv = document.getElementById('result');
            
            if (!schoolId) {
                resultDiv.innerHTML = '';
                return;
            }
            
            resultDiv.innerHTML = 'Loading...';
            
            fetch('/facilitator/ajax/school-classes/?school_id=' + schoolId)
                .then(response => response.json())
                .then(data => {
                    resultDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                })
                .catch(error => {
                    resultDiv.innerHTML = '<p style="color: red;">Error: ' + error + '</p>';
                });
        }
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html)

@facilitator_required
def facilitator_dashboard(request):
    """Enhanced facilitator dashboard with real data and analytics"""
    from django.db.models import Count, Avg, Q
    from .models import Attendance, ActualSession, PlannedSession
    from datetime import datetime, timedelta
    
    # Create mixin instance for access control
    mixin = FacilitatorAccessMixin()
    mixin.request = request
    
    # Get facilitator's schools and classes
    facilitator_schools = mixin.get_facilitator_schools()
    facilitator_classes = mixin.get_facilitator_classes()
    
    # Basic counts
    total_schools = facilitator_schools.count()
    total_classes = facilitator_classes.count()
    
    # Student counts
    total_students = Enrollment.objects.filter(
        school__in=facilitator_schools,
        is_active=True
    ).count()
    
    # Session statistics
    total_planned_sessions = PlannedSession.objects.filter(
        class_section__in=facilitator_classes,
        is_active=True
    ).count()
    
    conducted_sessions = ActualSession.objects.filter(
        planned_session__class_section__in=facilitator_classes,
        status='conducted'
    ).count()
    
    # Attendance statistics
    total_attendance_records = Attendance.objects.filter(
        enrollment__school__in=facilitator_schools
    ).count()
    
    present_count = Attendance.objects.filter(
        enrollment__school__in=facilitator_schools,
        status='present'
    ).count()
    
    # Calculate percentages
    session_completion_rate = (conducted_sessions / total_planned_sessions * 100) if total_planned_sessions > 0 else 0
    overall_attendance_rate = (present_count / total_attendance_records * 100) if total_attendance_records > 0 else 0
    
    # Recent activity (last 7 days)
    last_week = datetime.now().date() - timedelta(days=7)
    recent_sessions = ActualSession.objects.filter(
        planned_session__class_section__in=facilitator_classes,
        date__gte=last_week
    ).count()
    
    # Class-wise attendance rates
    class_attendance_stats = []
    for class_section in facilitator_classes[:5]:  # Top 5 classes
        class_total_attendance = Attendance.objects.filter(
            enrollment__class_section=class_section
        ).count()
        
        class_present_count = Attendance.objects.filter(
            enrollment__class_section=class_section,
            status='present'
        ).count()
        
        class_attendance_rate = (class_present_count / class_total_attendance * 100) if class_total_attendance > 0 else 0
        
        class_attendance_stats.append({
            'class_section': class_section,
            'attendance_rate': round(class_attendance_rate, 1),
            'total_students': Enrollment.objects.filter(
                class_section=class_section,
                is_active=True
            ).count()
        })
    
    # Recent students (last 5 added)
    recent_students = Enrollment.objects.filter(
        school__in=facilitator_schools,
        is_active=True
    ).select_related('student', 'class_section').order_by('-student__created_at')[:5]
    
    # Upcoming sessions (next 5)
    upcoming_sessions = PlannedSession.objects.filter(
        class_section__in=facilitator_classes,
        is_active=True
    ).exclude(
        actual_sessions__status='conducted'
    ).order_by('day_number')[:5]
    
    context = {
        # Basic stats
        'total_schools': total_schools,
        'total_classes': total_classes,
        'total_students': total_students,
        'total_planned_sessions': total_planned_sessions,
        'conducted_sessions': conducted_sessions,
        
        # Percentages
        'session_completion_rate': round(session_completion_rate, 1),
        'overall_attendance_rate': round(overall_attendance_rate, 1),
        
        # Recent activity
        'recent_sessions': recent_sessions,
        'recent_students': recent_students,
        'upcoming_sessions': upcoming_sessions,
        
        # Detailed stats
        'class_attendance_stats': class_attendance_stats,
        'facilitator_schools': facilitator_schools,
        
        # User info
        'facilitator_name': request.user.full_name,
        'facilitator_email': request.user.email,
    }
    
    return render(request, 'facilitator/dashboard.html', context)