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
from .student_performance_views import (
    student_performance_list, student_performance_detail, 
    student_performance_save, performance_cutoff_settings
)
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
        
        status_text = "Present" if status == 'present' else "Absent"
        messages.success(request, f"Office work attendance marked as {status_text}")
        
        return redirect("facilitator_today_session")
    
    messages.error(request, "Invalid request")
    return redirect("facilitator_today_session")


@facilitator_required
def facilitator_today_session_calendar(request):
    """
    Show today's session dashboard with calendar integration
    - Shows all facilitator's classes for today
    - For each class, shows if there's a session/holiday/office work scheduled
    - Integrates curriculum and session management
    """
    from datetime import date
    from .models import CalendarDate, SupervisorCalendar, OfficeWorkAttendance, PlannedSession, ActualSession, Attendance
    
    today = date.today()
    
    # Get facilitator's assigned schools using the correct relationship
    facilitator_schools = School.objects.filter(
        facilitators__facilitator=request.user,
        facilitators__is_active=True
    ).distinct()
    
    # Get facilitator's assigned classes
    facilitator_classes = ClassSection.objects.filter(
        school__in=facilitator_schools
    ).select_related('school').order_by('school__name', 'class_level', 'section')
    
    # Get ALL calendar entries for today
    calendar_dates_today = CalendarDate.objects.filter(
        date=today
    ).select_related('school', 'calendar__supervisor').prefetch_related('class_sections')
    
    # Create dicts for quick lookup of calendar entries
    calendar_by_class = {}  # class-level entries (grouped sessions)
    calendar_by_school = {}  # school-level entries (holidays, office work)
    
    for cal_date in calendar_dates_today:
        # For session type with class_sections (new ManyToMany field)
        if cal_date.date_type == 'session' and cal_date.class_sections.exists():
            for class_section in cal_date.class_sections.all():
                calendar_by_class[str(class_section.id)] = cal_date
        # Legacy: single class_section field (backward compatibility)
        elif cal_date.date_type == 'session' and cal_date.class_section:
            calendar_by_class[str(cal_date.class_section.id)] = cal_date
        
        # School-level entries (holidays, office work - not sessions)
        if cal_date.date_type in ['holiday', 'office_work'] and cal_date.school:
            calendar_by_school[str(cal_date.school.id)] = cal_date
    
    # Build classes with today's session info
    # Group classes that share the same calendar entry (same group created by supervisor)
    classes_today = []
    processed_calendar_ids = set()
    processed_class_ids = set()
    
    # First, identify which classes share the same calendar entry (new ManyToMany entries)
    # Also group legacy entries by school + date + type
    calendar_groups = {}  # key: calendar_entry_id or "legacy_school_date_type", value: list of classes
    
    for class_section in facilitator_classes:
        class_id_str = str(class_section.id)
        
        # Skip if already processed
        if class_id_str in processed_class_ids:
            continue
        
        school_id_str = str(class_section.school.id)
        
        # Check class-level entry first (grouped sessions), then school-level (holidays/office work)
        calendar_date = calendar_by_class.get(class_id_str) or calendar_by_school.get(school_id_str)
        
        if calendar_date:
            # Check if this is a new ManyToMany entry or legacy entry
            if calendar_date.class_sections.exists():
                # New ManyToMany entry - get all classes in this entry
                group_key = str(calendar_date.id)
                if group_key not in calendar_groups:
                    calendar_groups[group_key] = {
                        'classes': list(calendar_date.class_sections.all()),
                        'calendar_date': calendar_date,
                    }
            else:
                # Legacy entry - group by school + date + type
                group_key = f"legacy_{school_id_str}_{calendar_date.date}_{calendar_date.date_type}"
                if group_key not in calendar_groups:
                    # Find all classes from this school with calendar entries on the same date and type
                    legacy_classes = []
                    for other_class in facilitator_classes:
                        other_school_id_str = str(other_class.school.id)
                        if other_school_id_str == school_id_str:
                            other_calendar = calendar_by_class.get(str(other_class.id))
                            if other_calendar and other_calendar.date == calendar_date.date and other_calendar.date_type == calendar_date.date_type:
                                legacy_classes.append(other_class)
                    
                    calendar_groups[group_key] = {
                        'classes': legacy_classes,
                        'calendar_date': calendar_date,
                    }
        else:
            # No calendar entry for this class
            calendar_groups[f"no_entry_{class_id_str}"] = {
                'classes': [class_section],
                'calendar_date': None,
            }
    
    # Now build the output list from the groups
    for group_key, group_data in calendar_groups.items():
        grouped_classes = group_data['classes']
        calendar_date = group_data['calendar_date']
        
        # Mark all classes in this group as processed
        for cls in grouped_classes:
            processed_class_ids.add(str(cls.id))
        
        # Get planned session from first class in group
        planned_session = None
        actual_session = None
        attendance_summary = None
        
        if grouped_classes:
            # Use first class's session info
            first_class = grouped_classes[0]
            planned_session = PlannedSession.objects.filter(
                class_section=first_class,
                is_active=True
            ).first()
            
            if planned_session:
                actual_session = ActualSession.objects.filter(
                    planned_session=planned_session,
                    date=today
                ).first()
                
                # Get attendance summary if session was conducted
                if actual_session and actual_session.status == 'conducted':
                    attendance_summary = {
                        'present': Attendance.objects.filter(
                            actual_session=actual_session,
                            status='present'
                        ).count(),
                        'absent': Attendance.objects.filter(
                            actual_session=actual_session,
                            status='absent'
                        ).count(),
                        'leave': Attendance.objects.filter(
                            actual_session=actual_session,
                            status='leave'
                        ).count(),
                        'total': Attendance.objects.filter(
                            actual_session=actual_session
                        ).count(),
                    }
        
        # Determine status based on calendar
        status = 'no_session'
        if calendar_date:
            if calendar_date.date_type == 'session':
                status = 'session'
            elif calendar_date.date_type == 'holiday':
                status = 'holiday'
            elif calendar_date.date_type == 'office_work':
                status = 'office_work'
        
        # Add grouped classes as single entry
        classes_today.append({
            'class_sections': grouped_classes,  # List of grouped classes
            'class_section': grouped_classes[0] if grouped_classes else None,  # Primary class for display
            'planned_session': planned_session,
            'actual_session': actual_session,
            'calendar_date': calendar_date,
            'attendance_summary': attendance_summary,
            'status': status,
        })
    
    # Get office work for today (not tied to specific class)
    office_work_today = None
    office_work_calendar = CalendarDate.objects.filter(
        date=today,
        date_type='office_work'
    ).first()
    
    # Check if facilitator is assigned to office work
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
        date_type='holiday'
    ).first()
    
    if holiday_calendar:
        holiday_today = {
            'holiday_name': holiday_calendar.holiday_name,
        }
    
    # Logic: If ONLY office work exists (no sessions), hide classes
    # Check if there are any session entries for today
    has_any_sessions = CalendarDate.objects.filter(
        date=today,
        date_type='session'
    ).exists()
    
    # If office work is assigned AND no sessions exist, hide classes
    if is_assigned_to_office_work and not has_any_sessions:
        classes_today = []
    
    context = {
        'today': today,
        'classes_today': classes_today,
        'office_work_today': office_work_today,
        'holiday_today': holiday_today,
    }
    
    return render(request, 'facilitator/today_session_calendar.html', context)


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
    
    # Get class IDs from query parameter
    class_ids_str = request.GET.get('classes', '')
    if not class_ids_str:
        messages.error(request, "No classes specified")
        return redirect('facilitator_classes')
    
    class_ids = [cid.strip() for cid in class_ids_str.split(',') if cid.strip()]
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
    request.session['is_grouped_session'] = True
    request.session['grouped_class_ids'] = class_ids_str
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
