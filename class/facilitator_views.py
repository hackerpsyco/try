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
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import PermissionDenied
from .models import School, ClassSection, Student, Enrollment, FacilitatorSchool, User, SessionStatus, AttendanceStatus, DateType
from .mixins import FacilitatorAccessMixin
from .decorators import facilitator_required
from .forms import AddUserForm  # We'll need to create a student form
from .student_performance_views import (
    student_performance_list, student_performance_detail, 
    student_performance_save, performance_cutoff_settings
)
import logging
from datetime import date
import csv
import openpyxl
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
        from django.db.models import Count
        
        context = super().get_context_data(**kwargs)
        
        school_ids = [s.id for s in context['schools']]
        
        # OPTIMIZATION: Single batch query for both counts
        enrollment_counts = Enrollment.objects.filter(
            school_id__in=school_ids,
            is_active=True
        ).values('school_id').annotate(count=Count('id'))
        enrollment_by_school = {item['school_id']: item['count'] for item in enrollment_counts}
        
        class_counts = ClassSection.objects.filter(
            school_id__in=school_ids,
            is_active=True
        ).values('school_id').annotate(count=Count('id'))
        class_by_school = {item['school_id']: item['count'] for item in class_counts}
        
        schools_with_counts = [
            {
                'school': school,
                'enrollment_count': enrollment_by_school.get(school.id, 0),
                'class_count': class_by_school.get(school.id, 0)
            }
            for school in context['schools']
        ]
        
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
        from django.db.models import Count
        
        context = super().get_context_data(**kwargs)
        school = self.object
        
        classes = ClassSection.objects.filter(
            school=school,
            is_active=True
        ).order_by('class_level', 'section')
        
        class_ids = [c.id for c in classes]
        
        # OPTIMIZATION: Single batch query for enrollment counts
        enrollment_counts = Enrollment.objects.filter(
            class_section_id__in=class_ids,
            is_active=True
        ).values('class_section_id').annotate(count=Count('id'))
        enrollment_by_class = {item['class_section_id']: item['count'] for item in enrollment_counts}
        
        classes_with_counts = [
            {
                'class_section': cls,
                'enrollment_count': enrollment_by_class.get(cls.id, 0)
            }
            for cls in classes
        ]
        
        context['classes_with_counts'] = classes_with_counts
        
        grade_levels = classes.values_list('class_level', flat=True).distinct()
        context['grade_levels'] = sorted(set(grade_levels))
        
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
        from django.db.models import Count, Q, Prefetch
        from .models import Attendance, ActualSession
        
        context = super().get_context_data(**kwargs)
        
        context['schools'] = self.get_facilitator_schools()
        context['classes'] = self.get_assigned_class_sections()
        
        grade_levels = ClassSection.objects.filter(
            school__in=self.get_facilitator_schools()
        ).values_list('class_level', flat=True).distinct()
        context['grade_levels'] = sorted(set(grade_levels))
        
        context['filters'] = {
            'school': self.request.GET.get('school', ''),
            'class': self.request.GET.get('class', ''),
            'grade': self.request.GET.get('grade', ''),
            'search': self.request.GET.get('search', ''),
        }
        
        # OPTIMIZATION: Get all data in batch queries
        enrollment_ids = [e.id for e in context['enrollments']]
        class_ids = [c.id for c in context['classes']]
        
        # Single query for all class session counts
        class_session_counts = ActualSession.objects.filter(
            planned_session__class_section_id__in=class_ids,
            status=SessionStatus.CONDUCTED
        ).values('planned_session__class_section_id').annotate(count=Count('id'))
        
        class_session_dict = {
            item['planned_session__class_section_id']: item['count'] 
            for item in class_session_counts
        }
        
        # Single query for all attendance stats
        attendance_stats_raw = Attendance.objects.filter(
            enrollment_id__in=enrollment_ids
        ).values('enrollment_id').annotate(
            present_count=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
            absent_count=Count('id', filter=Q(status=AttendanceStatus.ABSENT))
        )
        
        attendance_by_enrollment = {
            stat['enrollment_id']: {
                'present': stat['present_count'],
                'absent': stat['absent_count']
            }
            for stat in attendance_stats_raw
        }
        
        # Build stats from batch queries
        enrollment_stats = []
        for enrollment in context['enrollments']:
            total_sessions = class_session_dict.get(enrollment.class_section_id, 0)
            attendance_data = attendance_by_enrollment.get(enrollment.id, {'present': 0, 'absent': 0})
            
            present_count = attendance_data['present']
            absent_count = attendance_data['absent']
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
    """View student details and attendance - OPTIMIZED"""
    from .models import Attendance, ActualSession
    
    student = get_object_or_404(Student, id=student_id)
    
    mixin = FacilitatorAccessMixin()
    mixin.request = request
    
    enrollment = Enrollment.objects.filter(
        student=student,
        is_active=True,
        school__in=mixin.get_facilitator_schools()
    ).first()
    
    if not enrollment:
        messages.error(request, "You do not have access to this student.")
        return redirect('facilitator_students_list')
    
    # OPTIMIZATION: Single aggregation query for attendance stats
    attendance_stats = Attendance.objects.filter(
        enrollment=enrollment
    ).aggregate(
        total_sessions=Count('id', filter=Q(status__in=[AttendanceStatus.PRESENT, AttendanceStatus.ABSENT])),
        present_count=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
        absent_count=Count('id', filter=Q(status=AttendanceStatus.ABSENT))
    )
    
    total_sessions = attendance_stats['total_sessions']
    present_count = attendance_stats['present_count']
    absent_count = attendance_stats['absent_count']
    attendance_percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0
    
    # Get recent attendance records with select_related
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
    """Enhanced facilitator dashboard with real data and analytics - OPTIMIZED"""
    from django.db.models import Count, Q, F, Case, When, IntegerField
    from .models import Attendance, ActualSession, PlannedSession
    from datetime import datetime, timedelta
    
    mixin = FacilitatorAccessMixin()
    mixin.request = request
    
    facilitator_schools = mixin.get_facilitator_schools()
    facilitator_classes = mixin.get_facilitator_classes()
    
    school_ids = list(facilitator_schools.values_list('id', flat=True))
    class_ids = list(facilitator_classes.values_list('id', flat=True))
    
    # OPTIMIZATION: Single aggregation query instead of multiple queries
    stats = PlannedSession.objects.filter(
        class_section_id__in=class_ids,
        is_active=True
    ).aggregate(
        total_planned=Count('id'),
        conducted=Count('id', filter=Q(actual_sessions__status=SessionStatus.CONDUCTED))
    )
    
    # OPTIMIZATION: Batch attendance stats in one query
    attendance_stats = Attendance.objects.filter(
        enrollment__school_id__in=school_ids
    ).aggregate(
        total_records=Count('id'),
        present_count=Count('id', filter=Q(status=AttendanceStatus.PRESENT))
    )
    
    total_planned_sessions = stats['total_planned']
    conducted_sessions = stats['conducted']
    total_attendance_records = attendance_stats['total_records']
    present_count = attendance_stats['present_count']
    
    session_completion_rate = (conducted_sessions / total_planned_sessions * 100) if total_planned_sessions > 0 else 0
    overall_attendance_rate = (present_count / total_attendance_records * 100) if total_attendance_records > 0 else 0
    
    # OPTIMIZATION: Get all class stats in one query with aggregation
    last_week = datetime.now().date() - timedelta(days=7)
    
    class_stats_raw = Attendance.objects.filter(
        enrollment__class_section_id__in=class_ids
    ).values('enrollment__class_section_id').annotate(
        total_attendance=Count('id'),
        present_attendance=Count('id', filter=Q(status=AttendanceStatus.PRESENT))
    )
    
    class_stats_dict = {
        stat['enrollment__class_section_id']: {
            'total': stat['total_attendance'],
            'present': stat['present_attendance']
        }
        for stat in class_stats_raw
    }
    
    # OPTIMIZATION: Get student counts per class in one query
    student_counts = Enrollment.objects.filter(
        class_section_id__in=class_ids,
        is_active=True
    ).values('class_section_id').annotate(count=Count('id'))
    
    student_counts_dict = {item['class_section_id']: item['count'] for item in student_counts}
    
    # Build class stats from aggregated data
    class_attendance_stats = []
    for class_section in facilitator_classes[:5]:
        stats_data = class_stats_dict.get(class_section.id, {'total': 0, 'present': 0})
        attendance_rate = (stats_data['present'] / stats_data['total'] * 100) if stats_data['total'] > 0 else 0
        
        class_attendance_stats.append({
            'class_section': class_section,
            'attendance_rate': round(attendance_rate, 1),
            'total_students': student_counts_dict.get(class_section.id, 0)
        })
    
    # OPTIMIZATION: Prefetch related data to avoid N+1
    recent_students = Enrollment.objects.filter(
        school_id__in=school_ids,
        is_active=True
    ).select_related('student', 'class_section').order_by('-student__created_at')[:5]
    
    recent_sessions = ActualSession.objects.filter(
        planned_session__class_section_id__in=class_ids,
        date__gte=last_week
    ).count()
    
    upcoming_sessions = PlannedSession.objects.filter(
        class_section_id__in=class_ids,
        is_active=True
    ).exclude(
        actual_sessions__status=SessionStatus.CONDUCTED
    ).order_by('day_number')[:5]
    
    context = {
        'total_schools': len(school_ids),
        'total_classes': len(class_ids),
        'total_students': Enrollment.objects.filter(school_id__in=school_ids, is_active=True).count(),
        'total_planned_sessions': total_planned_sessions,
        'conducted_sessions': conducted_sessions,
        'session_completion_rate': round(session_completion_rate, 1),
        'overall_attendance_rate': round(overall_attendance_rate, 1),
        'recent_sessions': recent_sessions,
        'recent_students': recent_students,
        'upcoming_sessions': upcoming_sessions,
        'class_attendance_stats': class_attendance_stats,
        'facilitator_schools': facilitator_schools,
        'facilitator_name': request.user.full_name,
        'facilitator_email': request.user.email,
    }
    
    return render(request, 'facilitator/dashboard.html', context)



# =====================================================
# TODAY'S SESSION WITH CALENDAR INTEGRATION
# =====================================================

@facilitator_required
def facilitator_today_session(request):
    """
    Redirect to facilitator classes list
    """
    return redirect('facilitator_classes')


@login_required
def facilitator_mark_office_work_attendance(request):
    """
    Mark office work attendance (present/absent)
    """
    from .models import CalendarDate, OfficeWorkAttendance
    from datetime import date
    
    if request.method == "POST":
        calendar_date_id = request.POST.get('calendar_date_id')
        status = request.POST.get('status')  # 'present' or 'absent'
        remarks = request.POST.get('remarks', '').strip()
        
        try:
            calendar_date = CalendarDate.objects.get(id=calendar_date_id)
        except CalendarDate.DoesNotExist:
            messages.error(request, "Invalid calendar date")
            return redirect("facilitator_today_session")
        
        if status not in ['present', 'absent']:
            messages.error(request, "Invalid status")
            return redirect("facilitator_today_session")
        
        # Create or update attendance record
        attendance, created = OfficeWorkAttendance.objects.update_or_create(
            calendar_date=calendar_date,
            facilitator=request.user,
            defaults={
                'status': status,
                'remarks': remarks,
            }
        )
        
        status_text = "Present" if status == AttendanceStatus.PRESENT else "Absent"
        messages.success(request, f"Office work attendance marked as {status_text}")
        
        return redirect("facilitator_today_session")
    
    messages.error(request, "Invalid request")
    return redirect("facilitator_today_session")


@facilitator_required
def facilitator_today_session_calendar(request):
    """
    Show today's session dashboard - OPTIMIZED
    - Only loads TODAY's sessions (not all 700+)
    - Uses prefetch_related to avoid N+1 queries
    - Batch queries for attendance data
    """
    from datetime import date
    from django.db.models import Count, Q, Prefetch
    from .models import CalendarDate, OfficeWorkAttendance, PlannedSession, ActualSession, Attendance
    
    today = date.today()
    
    # Get facilitator's schools (single query)
    facilitator_schools = School.objects.filter(
        facilitators__facilitator=request.user,
        facilitators__is_active=True
    ).values_list('id', flat=True)
    
    # OPTIMIZATION: Only query TODAY's calendar entries with prefetch
    calendar_sessions_today = CalendarDate.objects.filter(
        date=today,
        date_type=DateType.SESSION
    ).select_related('school', 'calendar__supervisor').prefetch_related('class_sections')
    
    classes_today = []
    processed_calendar_ids = set()
    actual_session_ids = []
    
    # First pass: collect actual session IDs for batch query
    for calendar_date in calendar_sessions_today:
        calendar_id = str(calendar_date.id)
        if calendar_id in processed_calendar_ids:
            continue
        processed_calendar_ids.add(calendar_id)
        
        grouped_classes = list(calendar_date.class_sections.all()) if calendar_date.class_sections.exists() else []
        facilitator_grouped_classes = [cls for cls in grouped_classes if cls.school_id in facilitator_schools]
        
        if not facilitator_grouped_classes:
            continue
        
        first_class = facilitator_grouped_classes[0]
        
        # Query actual sessions for today only
        actual_session = ActualSession.objects.filter(
            planned_session__class_section=first_class,
            date=today
        ).select_related('planned_session').first()
        
        if actual_session:
            actual_session_ids.append(actual_session.id)
            classes_today.append({
                'class_sections': facilitator_grouped_classes,
                'class_section': first_class,
                'planned_session': actual_session.planned_session,
                'actual_session': actual_session,
                'calendar_date': calendar_date,
                'attendance_summary': None,  # Will fill in batch query
                'status': 'session',
            })
    
    # OPTIMIZATION: Batch query all attendance data for today's sessions
    if actual_session_ids:
        attendance_summaries = Attendance.objects.filter(
            actual_session_id__in=actual_session_ids
        ).values('actual_session_id', 'status').annotate(count=Count('id'))
        
        attendance_dict = {}
        for record in attendance_summaries:
            session_id = record['actual_session_id']
            if session_id not in attendance_dict:
                attendance_dict[session_id] = {'present': 0, 'absent': 0, 'leave': 0, 'total': 0}
            
            status = record['status']
            count = record['count']
            if status == AttendanceStatus.PRESENT:
                attendance_dict[session_id]['present'] = count
            elif status == AttendanceStatus.ABSENT:
                attendance_dict[session_id]['absent'] = count
            elif status == AttendanceStatus.LEAVE:
                attendance_dict[session_id]['leave'] = count
            attendance_dict[session_id]['total'] += count
        
        # Update classes_today with attendance summaries
        for item in classes_today:
            session_id = item['actual_session'].id
            if session_id in attendance_dict:
                item['attendance_summary'] = attendance_dict[session_id]
    
    # Get office work for today
    office_work_today = None
    office_work_calendar = CalendarDate.objects.filter(
        date=today,
        date_type=DateType.OFFICE_WORK
    ).select_related('calendar__supervisor').prefetch_related('assigned_facilitators').first()
    
    is_assigned_to_office_work = False
    if office_work_calendar:
        is_assigned_to_office_work = office_work_calendar.assigned_facilitators.filter(id=request.user.id).exists()
        
        if is_assigned_to_office_work:
            office_attendance = OfficeWorkAttendance.objects.filter(
                calendar_date=office_work_calendar,
                facilitator=request.user
            ).first()
            
            office_work_today = {
                'calendar_date': office_work_calendar,
                'is_assigned': True,
                'attendance': office_attendance,
            }
    
    # Get holiday for today
    holiday_today = None
    holiday_calendar = CalendarDate.objects.filter(
        date=today,
        date_type=DateType.HOLIDAY
    ).first()
    
    if holiday_calendar:
        holiday_today = {'holiday_name': holiday_calendar.holiday_name}
    
    # Get facilitator's schools and classes (with select_related)
    facilitator_schools_list = School.objects.filter(
        facilitators__facilitator=request.user,
        facilitators__is_active=True
    ).order_by('name')
    
    facilitator_classes = ClassSection.objects.filter(
        school__in=facilitator_schools_list
    ).select_related('school').order_by('school__name', 'class_level', 'section')
    
    context = {
        'today': today,
        'classes_today': classes_today,
        'office_work_today': office_work_today,
        'holiday_today': holiday_today,
        'facilitator_schools': facilitator_schools_list,
        'facilitator_classes': facilitator_classes,
        'total_sessions_today': len(classes_today),
        'has_office_work': is_assigned_to_office_work,
        'has_holiday': holiday_today is not None,
    }
    
    return render(request, 'facilitator/Today_session.html', context)


@facilitator_required
def facilitator_performance_class_select(request):
    """
    Show all classes assigned to facilitator for performance management
    """
    from .models import StudentPerformanceSummary, Subject
    
    # Get all classes assigned to this facilitator
    facilitator_schools = FacilitatorSchool.objects.filter(
        facilitator=request.user,
        is_active=True
    ).values_list('school_id', flat=True)
    
    classes = ClassSection.objects.filter(
        school_id__in=facilitator_schools,
        is_active=True
    ).order_by('school__name', 'class_level', 'section')
    
    # Add stats for each class
    classes_with_stats = []
    for class_section in classes:
        student_count = Enrollment.objects.filter(
            class_section=class_section,
            is_active=True
        ).count()
        
        performance_count = StudentPerformanceSummary.objects.filter(
            class_section=class_section
        ).count()
        
        subject_count = Subject.objects.filter(is_active=True).count()
        
        classes_with_stats.append({
            'id': class_section.id,
            'display_name': class_section.display_name,
            'school_name': class_section.school.name,
            'student_count': student_count,
            'performance_count': performance_count,
            'subject_count': subject_count,
        })
    
    context = {
        'classes': classes_with_stats,
    }
    
    return render(request, 'facilitator/performance/class_select.html', context)



@facilitator_required
def facilitator_grouped_session(request):
    """
    Handle grouped session view - redirects to today_session with grouped class info
    Classes are passed as query parameter: ?classes=id1,id2,id3
    Stores grouped class info in session, then redirects to primary class today_session
    """
    from datetime import date
    import uuid
    
    # Get class IDs from query parameter
    class_ids_str = request.GET.get('classes', '')
    if not class_ids_str:
        messages.error(request, "No classes specified")
        return redirect('facilitator_classes')
    
    # Parse and validate UUIDs
    class_ids = []
    for cid in class_ids_str.split(','):
        cid = cid.strip()
        if cid:
            try:
                # Validate UUID format
                uuid.UUID(cid)
                class_ids.append(cid)
            except ValueError:
                messages.error(request, f"Invalid class ID format: {cid}")
                return redirect('facilitator_classes')
    
    if not class_ids:
        messages.error(request, "Invalid class IDs")
        return redirect('facilitator_classes')
    
    # Get all grouped classes
    grouped_classes = ClassSection.objects.filter(
        id__in=class_ids
    ).select_related('school').order_by('class_level', 'section')
    
    if not grouped_classes.exists():
        messages.error(request, "Classes not found")
        return redirect('facilitator_classes')
    
    # Verify facilitator has access to all classes
    mixin = FacilitatorAccessMixin()
    mixin.request = request
    facilitator_schools = mixin.get_facilitator_schools()
    
    for cls in grouped_classes:
        if cls.school not in facilitator_schools:
            messages.error(request, "You do not have access to one or more classes")
            return redirect('facilitator_classes')
    
    # Get primary class (first in group)
    primary_class = grouped_classes.first()
    
    # Store grouped class info in session for display in today_session template
    # Store as list of UUID strings for consistency
    request.session['is_grouped_session'] = True
    request.session['grouped_class_ids'] = [str(cls.id) for cls in grouped_classes]
    request.session['grouped_classes_display'] = [
        {'id': str(cls.id), 'display_name': cls.display_name} 
        for cls in grouped_classes
    ]
    
    # Redirect to primary class today_session view
    # The today_session view will use the session data to show grouped class info
    return redirect('facilitator_class_today_session', class_section_id=primary_class.id)


# =====================================================
# Facilitator Settings
# =====================================================

@facilitator_required
def facilitator_settings(request):
    """Facilitator settings page"""
    return render(request, "facilitator/settings.html", {})


# =====================================================
# BULK STUDENT IMPORT FUNCTIONS
# =====================================================

@login_required
@facilitator_required
def facilitator_student_import(request, class_section_id):
    """Bulk import students via CSV/Excel for a specific class"""
    class_section = get_object_or_404(ClassSection, id=class_section_id)
    
    # Check access - facilitator must have access to this class
    mixin = FacilitatorAccessMixin()
    mixin.request = request
    if not mixin.check_class_access(class_section_id):
        raise PermissionDenied("You don't have access to this class")
    
    if request.method == "POST":
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "Please upload a file")
            return redirect(request.path)
        
        ext = file.name.split(".")[-1].lower()
        
        # Parse file
        if ext == "csv":
            rows = csv.DictReader(file.read().decode("utf-8").splitlines())
        elif ext in ["xlsx", "xls"]:
            wb = openpyxl.load_workbook(file)
            sheet = wb.active
            headers = [str(cell.value).strip() for cell in sheet[1]]
            rows = []
            for r in sheet.iter_rows(min_row=2, values_only=True):
                rows.append(dict(zip(headers, r)))
        else:
            messages.error(request, "Unsupported file format. Use CSV or Excel.")
            return redirect(request.path)
        
        created_count = 0
        skipped_count = 0
        
        # Process rows
        for row in rows:
            enrollment_no = str(row.get("enrollment_number", "")).strip()
            full_name = str(row.get("full_name", "")).strip()
            gender = str(row.get("gender", "")).strip()
            start_date = row.get("start_date") or date.today()
            
            # Validate
            if not all([enrollment_no, full_name, gender]):
                skipped_count += 1
                continue
            
            if gender.upper() not in ["M", "F"]:
                skipped_count += 1
                continue
            
            # Create student
            student, _ = Student.objects.get_or_create(
                enrollment_number=enrollment_no,
                defaults={
                    "full_name": full_name,
                    "gender": gender.upper()
                }
            )
            
            # Create enrollment
            enrollment, created = Enrollment.objects.get_or_create(
                student=student,
                school=class_section.school,
                class_section=class_section,
                defaults={
                    "start_date": start_date,
                    "is_active": True
                }
            )
            
            if created:
                created_count += 1
        
        # Feedback
        if created_count == 0:
            messages.warning(request, f"No students imported. Skipped: {skipped_count}")
        else:
            messages.success(request, f"{created_count} students imported (Skipped: {skipped_count})")
        
        return redirect("facilitator_class_students", class_section_id=class_section_id)
    
    return render(request, "facilitator/students/import.html", {
        "class_section": class_section
    })


@login_required
@facilitator_required
def facilitator_download_sample_csv(request):
    """Download sample CSV for student import"""
    sample_data = [
        ["enrollment_number", "full_name", "gender", "start_date"],
        ["E001", "John Doe", "M", "2026-01-12"],
        ["E002", "Jane Smith", "F", "2026-01-12"],
    ]
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students_sample.csv"'
    
    writer = csv.writer(response)
    for row in sample_data:
        writer.writerow(row)
    
    return response
