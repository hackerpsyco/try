# Supervisor Views - Complete Management Interface
import uuid
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q, Prefetch
from django.core.cache import cache
from django.db import transaction
from .models import User, Role, School, ClassSection, FacilitatorSchool, PlannedSession, DateType
from .forms import AddUserForm, EditUserForm, AddSchoolForm, ClassSectionForm, AssignFacilitatorForm

User = get_user_model()
logger = logging.getLogger(__name__)

# =====================================================
# Helper Functions for Grouped Sessions
# =====================================================
def initialize_grouped_session_plans(classes, grouped_session_id):
    """
    Initialize 150-day session plans for grouped classes.
    
    - Creates ONE shared 150-day plan for the primary class
    - Creates placeholder sessions for other classes that reference the same grouped_session_id
    - Deletes any existing individual session plans for these classes
    """
    if not classes:
        return {'success': False, 'error': 'No classes provided'}
    
    try:
        with transaction.atomic():
            primary_class = classes[0]
            
            # Delete any existing individual session plans for ALL classes in the group
            # (they will now share ONE grouped session)
            PlannedSession.objects.filter(
                class_section__in=classes
            ).delete()
            
            # Create ONE shared 150-day session plan for the primary class
            sessions_to_create = []
            for day_number in range(1, 151):
                session = PlannedSession(
                    class_section=primary_class,
                    day_number=day_number,
                    title=f"Day {day_number} Session",
                    description=f"Grouped session for {', '.join([c.display_name for c in classes])}",
                    sequence_position=day_number,
                    is_required=True,
                    is_active=True,
                    grouped_session_id=grouped_session_id
                )
                sessions_to_create.append(session)
            
            # Bulk create all sessions for primary class
            PlannedSession.objects.bulk_create(sessions_to_create)
            
            # Create placeholder sessions for other classes that reference the same grouped_session_id
            for cls in classes[1:]:
                placeholder_sessions = []
                for day_number in range(1, 151):
                    session = PlannedSession(
                        class_section=cls,
                        day_number=day_number,
                        title=f"Day {day_number} Session",
                        description=f"Grouped session for {', '.join([c.display_name for c in classes])}",
                        sequence_position=day_number,
                        is_required=True,
                        is_active=True,
                        grouped_session_id=grouped_session_id
                    )
                    placeholder_sessions.append(session)
                
                # Bulk create placeholder sessions for this class
                PlannedSession.objects.bulk_create(placeholder_sessions)
            
            return {
                'success': True,
                'message': f'Created 150-day grouped session plan for {len(classes)} classes',
                'classes_count': len(classes),
                'sessions_created': 150 * len(classes)
            }
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

# =====================================================
# Permission Decorator for Supervisor
# =====================================================
def supervisor_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role.name.upper() != "SUPERVISOR":
            messages.error(request, "You do not have permission to access this page.")
            return redirect("no_permission")
        return view_func(request, *args, **kwargs)
    return wrapper

# =====================================================
# Dashboard
# =====================================================
@login_required
@supervisor_required
def supervisor_dashboard(request):
    """Supervisor Dashboard - Overview of all managed resources"""
    
    # Get statistics
    total_users = User.objects.count()
    total_schools = School.objects.count()
    total_classes = ClassSection.objects.count()
    active_facilitators = User.objects.filter(
        role__name__iexact="FACILITATOR",
        is_active=True
    ).count()
    
    # Recent users
    recent_users = User.objects.all().order_by("-created_at")[:5]
    
    # Recent schools
    recent_schools = School.objects.all().order_by("-created_at")[:5]
    
    context = {
        'total_users': total_users,
        'total_schools': total_schools,
        'total_classes': total_classes,
        'active_facilitators': active_facilitators,
        'recent_users': recent_users,
        'recent_schools': recent_schools,
    }
    
    return render(request, "supervisor/dashboard.html", context)

# =====================================================
# User Management
# =====================================================
@login_required
@supervisor_required
def supervisor_users_list(request):
    """List all users with filtering"""
    
    users = User.objects.all().select_related('role').order_by("-created_at")
    
    # Filter by role
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role__id=role_filter)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    roles = Role.objects.all()
    
    context = {
        'users': users,
        'roles': roles,
        'selected_role': role_filter,
        'selected_status': status_filter,
    }
    
    return render(request, "supervisor/users/list.html", context)

@login_required
@supervisor_required
def supervisor_user_create(request):
    """Create new user with role assignment"""
    
    if request.method == "POST":
        form = AddUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, f"User '{user.full_name}' created successfully!")
            return redirect("supervisor_users_list")
    else:
        form = AddUserForm()
    
    return render(request, "supervisor/users/create.html", {"form": form})

@login_required
@supervisor_required
def supervisor_user_edit(request, user_id):
    """Edit user details"""
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        form = EditUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{user.full_name}' updated successfully!")
            return redirect("supervisor_users_list")
    else:
        form = EditUserForm(instance=user)
    
    return render(request, "supervisor/users/edit.html", {
        "form": form,
        "user": user
    })

@login_required
@supervisor_required
def supervisor_user_delete(request, user_id):
    """Delete user"""
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        user_name = user.full_name
        user.delete()
        messages.success(request, f"User '{user_name}' deleted successfully!")
        return redirect("supervisor_users_list")
    
    return render(request, "supervisor/users/delete_confirm.html", {"user": user})

# =====================================================
# School Management
# =====================================================
@login_required
@supervisor_required
def supervisor_schools_list(request):
    """List all schools"""
    
    cache_key = f"supervisor_schools_list_{request.user.id}"
    schools = cache.get(cache_key)
    
    if schools is None:
        schools = School.objects.select_related().prefetch_related(
            Prefetch(
                'class_sections',
                queryset=ClassSection.objects.select_related().annotate(
                    student_count=Count('enrollments', filter=Q(enrollments__is_active=True))
                )
            ),
            Prefetch(
                'facilitators',
                queryset=FacilitatorSchool.objects.select_related('facilitator').filter(is_active=True)
            )
        ).annotate(
            total_classes=Count('class_sections', distinct=True),
            total_students=Count('class_sections__enrollments', 
                               filter=Q(class_sections__enrollments__is_active=True),
                               distinct=True),
            active_facilitators=Count('facilitators', 
                                    filter=Q(facilitators__is_active=True),
                                    distinct=True)
        ).order_by("-created_at")
        
        cache.set(cache_key, schools, 300)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        schools = schools.filter(status=int(status_filter))
    
    context = {
        'schools': schools,
        'selected_status': status_filter,
    }
    
    return render(request, "supervisor/schools/list.html", context)

@login_required
@supervisor_required
def supervisor_school_create(request):
    """Create new school"""
    
    if request.method == "POST":
        form = AddSchoolForm(request.POST, request.FILES)
        if form.is_valid():
            school = form.save()
            cache_key = f"supervisor_schools_list_{request.user.id}"
            cache.delete(cache_key)
            messages.success(request, f"School '{school.name}' created successfully!")
            return redirect("supervisor_schools_list")
    else:
        form = AddSchoolForm()
    
    return render(request, "supervisor/schools/create.html", {"form": form})

@login_required
@supervisor_required
def supervisor_school_edit(request, school_id):
    """Edit school details"""
    
    school = get_object_or_404(School, id=school_id)
    
    if request.method == "POST":
        form = AddSchoolForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            school = form.save()
            cache_key = f"supervisor_schools_list_{request.user.id}"
            cache.delete(cache_key)
            messages.success(request, f"School '{school.name}' updated successfully!")
            return redirect("supervisor_schools_list")
    else:
        form = AddSchoolForm(instance=school)
    
    return render(request, "supervisor/schools/edit.html", {
        "form": form,
        "school": school
    })

@login_required
@supervisor_required
def supervisor_school_detail(request, school_id):
    """View school details"""
    
    school = get_object_or_404(School, id=school_id)
    classes = ClassSection.objects.filter(school=school).order_by("class_level", "section")
    facilitators = FacilitatorSchool.objects.filter(school=school).select_related("facilitator")
    
    context = {
        'school': school,
        'classes': classes,
        'facilitators': facilitators,
    }
    
    return render(request, "supervisor/schools/detail.html", context)

@login_required
@supervisor_required
def supervisor_school_delete(request, school_id):
    """Delete school"""
    
    school = get_object_or_404(School, id=school_id)
    
    if request.method == "POST":
        school_name = school.name
        school.delete()
        cache_key = f"supervisor_schools_list_{request.user.id}"
        cache.delete(cache_key)
        messages.success(request, f"School '{school_name}' deleted successfully!")
        return redirect("supervisor_schools_list")
    
    return render(request, "supervisor/schools/delete_confirm.html", {"school": school})

# =====================================================
# Class Management
# =====================================================
@login_required
@supervisor_required
def supervisor_classes_list(request):
    """List all classes"""
    
    classes = ClassSection.objects.select_related('school').order_by("school__name", "class_level", "section")
    
    # Filter by school
    school_filter = request.GET.get('school')
    if school_filter:
        classes = classes.filter(school__id=school_filter)
    
    schools = School.objects.all()
    
    context = {
        'classes': classes,
        'schools': schools,
        'selected_school': school_filter,
    }
    
    return render(request, "supervisor/classes/list.html", context)

# =====================================================
# Reports & Analytics
# =====================================================
@login_required
@supervisor_required
def supervisor_reports_dashboard(request):
    """Reports and analytics dashboard"""
    
    # Get statistics
    total_users = User.objects.count()
    total_schools = School.objects.count()
    total_classes = ClassSection.objects.count()
    
    # User breakdown by role
    user_by_role = User.objects.values('role__name').annotate(count=Count('id'))
    
    # Schools by status
    schools_by_status = School.objects.values('status').annotate(count=Count('id'))
    
    context = {
        'total_users': total_users,
        'total_schools': total_schools,
        'total_classes': total_classes,
        'user_by_role': user_by_role,
        'schools_by_status': schools_by_status,
    }
    
    return render(request, "supervisor/reports/dashboard.html", context)

@login_required
@supervisor_required
def supervisor_feedback_analytics(request):
    """Feedback analytics"""
    
    context = {}
    return render(request, "supervisor/reports/feedback.html", context)

# =====================================================
# Settings
# =====================================================
@login_required
@supervisor_required
def supervisor_settings(request):
    """Supervisor settings"""
    
    return render(request, "supervisor/settings.html", {})

# =====================================================
# AJAX Endpoints
# =====================================================
@csrf_exempt
@login_required
@supervisor_required
def supervisor_create_user_ajax(request):
    """AJAX endpoint for creating users"""
    
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role_id = request.POST.get("role")
        
        if not all([full_name, email, password, role_id]):
            return JsonResponse({"success": False, "error": "All fields are required."})
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({"success": False, "error": "User already exists."})
        
        try:
            role = Role.objects.get(id=role_id)
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role=role
            )
            
            return JsonResponse({
                "success": True,
                "user": {
                    "id": str(user.id),
                    "full_name": user.full_name,
                    "email": user.email,
                    "role_name": role.name
                }
            })
        
        except Role.DoesNotExist:
            return JsonResponse({"success": False, "error": "Invalid role selected."})
    
    return JsonResponse({"success": False, "error": "Invalid request method."})

# =====================================================
# Facilitator Management
# =====================================================
@login_required
@supervisor_required
def supervisor_facilitators_list(request):
    """List all facilitators with their details"""
    
    facilitators = User.objects.filter(
        role__name__iexact="FACILITATOR"
    ).select_related('role').prefetch_related(
        Prefetch(
            'assigned_schools',
            queryset=FacilitatorSchool.objects.select_related('school').filter(is_active=True)
        )
    ).annotate(
        school_count=Count('assigned_schools', filter=Q(assigned_schools__is_active=True), distinct=True)
    ).order_by("-created_at")
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        facilitators = facilitators.filter(is_active=True)
    elif status_filter == 'inactive':
        facilitators = facilitators.filter(is_active=False)
    
    context = {
        'facilitators': facilitators,
        'selected_status': status_filter,
    }
    
    return render(request, "supervisor/facilitators/list.html", context)

@login_required
@supervisor_required
def supervisor_facilitator_detail(request, facilitator_id):
    """View facilitator profile and their work"""
    
    facilitator = get_object_or_404(User, id=facilitator_id, role__name__iexact="FACILITATOR")
    
    # Get facilitator's schools
    facilitator_schools = FacilitatorSchool.objects.filter(
        facilitator=facilitator,
        is_active=True
    ).select_related('school')
    
    # Get facilitator's classes from assigned schools
    school_ids = facilitator_schools.values_list('school_id', flat=True)
    facilitator_classes = ClassSection.objects.filter(
        school_id__in=school_ids
    ).select_related('school').order_by('school__name', 'class_level', 'section')
    
    # Get facilitator's students from their schools
    from django.db.models import Prefetch
    from .models import Student, Enrollment
    facilitator_students = Student.objects.filter(
        enrollments__class_section__school_id__in=school_ids,
        enrollments__is_active=True
    ).distinct().order_by('full_name')
    
    # Get facilitator's sessions from their schools
    from .models import PlannedSession
    facilitator_sessions = PlannedSession.objects.filter(
        class_section__school_id__in=school_ids
    ).select_related('class_section', 'class_section__school').order_by('-created_at')[:10]
    
    # Get facilitator's tasks (preparation media)
    from .models import FacilitatorTask
    facilitator_tasks = FacilitatorTask.objects.filter(
        facilitator=facilitator
    ).select_related('actual_session', 'actual_session__planned_session', 'actual_session__planned_session__class_section').order_by('-created_at')[:20]
    
    context = {
        'facilitator': facilitator,
        'schools': facilitator_schools,
        'classes': facilitator_classes,
        'students': facilitator_students,
        'recent_sessions': facilitator_sessions,
        'facilitator_tasks': facilitator_tasks,
        'school_count': facilitator_schools.count(),
        'class_count': facilitator_classes.count(),
        'student_count': facilitator_students.count(),
        'task_count': facilitator_tasks.count(),
    }
    
    return render(request, "supervisor/facilitators/detail.html", context)

@login_required
@supervisor_required
def supervisor_assign_facilitator_school(request, facilitator_id):
    """Assign facilitator to schools"""
    
    facilitator = get_object_or_404(User, id=facilitator_id, role__name__iexact="FACILITATOR")
    
    if request.method == "POST":
        school_ids = request.POST.getlist('schools')
        
        # Clear existing assignments
        FacilitatorSchool.objects.filter(facilitator=facilitator).delete()
        
        # Create new assignments
        for school_id in school_ids:
            try:
                school = School.objects.get(id=school_id)
                FacilitatorSchool.objects.create(
                    facilitator=facilitator,
                    school=school,
                    is_active=True
                )
            except School.DoesNotExist:
                pass
        
        messages.success(request, f"Facilitator '{facilitator.full_name}' assigned to schools successfully!")
        return redirect("supervisor_facilitator_detail", facilitator_id=facilitator_id)
    
    # Get all schools and currently assigned schools
    all_schools = School.objects.all().order_by('name')
    assigned_schools = FacilitatorSchool.objects.filter(
        facilitator=facilitator,
        is_active=True
    ).values_list('school_id', flat=True)
    
    context = {
        'facilitator': facilitator,
        'all_schools': all_schools,
        'assigned_schools': assigned_schools,
    }
    
    return render(request, "supervisor/facilitators/assign_schools.html", context)

@login_required
@supervisor_required
def supervisor_assign_facilitator_class(request, facilitator_id):
    """View classes in facilitator's assigned schools"""
    
    facilitator = get_object_or_404(User, id=facilitator_id, role__name__iexact="FACILITATOR")
    
    # Get facilitator's assigned schools
    assigned_schools = FacilitatorSchool.objects.filter(
        facilitator=facilitator,
        is_active=True
    ).values_list('school_id', flat=True)
    
    # Get all classes from assigned schools
    all_classes = ClassSection.objects.filter(
        school_id__in=assigned_schools
    ).select_related('school').order_by('school__name', 'class_level', 'section')
    
    context = {
        'facilitator': facilitator,
        'all_classes': all_classes,
        'assigned_schools': assigned_schools,
    }
    
    return render(request, "supervisor/facilitators/view_classes.html", context)


# =====================================================
# Class Management for Supervisor
# =====================================================
@login_required
@supervisor_required
def supervisor_class_create(request):
    """Create new class - Supervisor can add classes"""
    
    if request.method == "POST":
        form = ClassSectionForm(request.POST)
        if form.is_valid():
            class_section = form.save()
            messages.success(request, f"Class '{class_section.class_level} {class_section.section}' created successfully!")
            return redirect("supervisor_classes_list")
    else:
        form = ClassSectionForm()
    
    context = {
        'form': form,
        'title': 'Add New Class'
    }
    
    return render(request, "supervisor/classes/create.html", context)


@login_required
@supervisor_required
def supervisor_class_bulk_create(request):
    """Bulk create multiple classes at once"""
    
    schools = School.objects.all().order_by('name')
    class_levels = list(range(1, 11))  # Classes 1-10
    
    if request.method == "POST":
        school_id = request.POST.get('school')
        class_levels_selected = request.POST.getlist('class_levels')
        section = request.POST.get('section', 'A')
        academic_year = request.POST.get('academic_year', '2024-2025')
        
        if not school_id or not class_levels_selected:
            messages.error(request, "Please select a school and at least one class level")
            return redirect("supervisor_class_bulk_create")
        
        try:
            school = School.objects.get(id=school_id)
            created_count = 0
            
            for level in class_levels_selected:
                # Check if class already exists
                existing = ClassSection.objects.filter(
                    school=school,
                    class_level=level,
                    section=section,
                    academic_year=academic_year
                ).exists()
                
                if not existing:
                    ClassSection.objects.create(
                        school=school,
                        class_level=level,
                        section=section,
                        academic_year=academic_year,
                        is_active=True
                    )
                    created_count += 1
            
            if created_count > 0:
                messages.success(request, f"Successfully created {created_count} class(es) in {school.name}")
            else:
                messages.warning(request, "All selected classes already exist")
            
            return redirect("supervisor_classes_list")
        
        except School.DoesNotExist:
            messages.error(request, "School not found")
            return redirect("supervisor_class_bulk_create")
    
    context = {
        'schools': schools,
        'class_levels': class_levels,
    }
    
    return render(request, "supervisor/classes/bulk_create.html", context)


@login_required
@supervisor_required
def supervisor_class_edit(request, class_id):
    """Edit class details - Supervisor can edit classes"""
    
    class_section = get_object_or_404(ClassSection, id=class_id)
    
    if request.method == "POST":
        form = ClassSectionForm(request.POST, instance=class_section)
        if form.is_valid():
            class_section = form.save()
            messages.success(request, f"Class '{class_section.class_level} {class_section.section}' updated successfully!")
            return redirect("supervisor_classes_list")
    else:
        form = ClassSectionForm(instance=class_section)
    
    context = {
        'form': form,
        'class_section': class_section,
        'title': 'Edit Class'
    }
    
    return render(request, "supervisor/classes/edit.html", context)


@login_required
@supervisor_required
def supervisor_class_delete(request, class_id):
    """Delete class - Supervisor can delete classes"""
    
    class_section = get_object_or_404(ClassSection, id=class_id)
    
    if request.method == "POST":
        class_name = f"{class_section.class_level} {class_section.section}"
        class_section.delete()
        messages.success(request, f"Class '{class_name}' deleted successfully!")
        return redirect("supervisor_classes_list")
    
    context = {
        'class_section': class_section,
    }
    
    return render(request, "supervisor/classes/delete_confirm.html", context)


@login_required
@supervisor_required
def supervisor_bulk_add_classes(request):
    """Bulk add multiple classes - Show form to add classes in group"""
    
    # Get selected class IDs from query params or session
    selected_ids = request.GET.getlist('ids')
    
    if not selected_ids:
        messages.error(request, "No classes selected")
        return redirect("supervisor_classes_list")
    
    # Get the selected classes
    selected_classes = ClassSection.objects.filter(
        id__in=selected_ids
    ).select_related('school').order_by('school__name', 'class_level', 'section')
    
    if request.method == "POST":
        # Get form data
        class_name = request.POST.get('class_name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not class_name:
            messages.error(request, "Class name is required")
            return render(request, "supervisor/classes/bulk_add.html", {
                'selected_classes': selected_classes,
                'selected_ids': selected_ids,
            })
        
        # Here you can add logic to create a group or perform bulk operations
        # For now, just show success message
        messages.success(request, f"Successfully processed {len(selected_classes)} classes")
        return redirect("supervisor_classes_list")
    
    context = {
        'selected_classes': selected_classes,
        'selected_ids': ','.join(selected_ids),
        'class_count': len(selected_classes),
    }
    
    return render(request, "supervisor/classes/bulk_add.html", context)



# =====================================================
# CALENDAR MANAGEMENT
# =====================================================

@login_required
@supervisor_required
def supervisor_calendar(request):
    """Supervisor Calendar - View and manage calendar dates"""
    from datetime import datetime, timedelta
    from .models import SupervisorCalendar, CalendarDate
    
    # Get or create supervisor calendar
    calendar, created = SupervisorCalendar.objects.get_or_create(
        supervisor=request.user
    )
    
    # Get current month
    today = datetime.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    # Get all dates for this month
    from datetime import date
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    
    calendar_dates = CalendarDate.objects.filter(
        calendar=calendar,
        date__gte=first_day,
        date__lte=last_day
    ).select_related('class_section', 'school').prefetch_related('assigned_facilitators')
    
    # Create a dict for easy lookup - store ALL entries for each date
    dates_dict = {}
    for cd in calendar_dates:
        if cd.date not in dates_dict:
            dates_dict[cd.date] = []
        dates_dict[cd.date].append(cd)
    
    # Build calendar grid
    calendar_grid = []
    current_date = first_day
    week = []
    
    # Add empty cells for days before month starts
    for _ in range(current_date.weekday()):
        week.append(None)
    
    while current_date <= last_day:
        week.append({
            'date': current_date,
            'calendar_date': dates_dict.get(current_date),
        })
        
        if len(week) == 7:
            calendar_grid.append(week)
            week = []
        
        current_date += timedelta(days=1)
    
    # Add remaining empty cells
    if week:
        while len(week) < 7:
            week.append(None)
        calendar_grid.append(week)
    
    # Navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    context = {
        'calendar': calendar,
        'calendar_grid': calendar_grid,
        'current_month': month,
        'current_year': year,
        'month_name': first_day.strftime('%B'),
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'today': today,
    }
    
    return render(request, "supervisor/calendar/calendar.html", context)


@login_required
@supervisor_required
def supervisor_calendar_add_date(request):
    """Add a date to calendar (session, holiday, or office work) with bulk support"""
    from .models import SupervisorCalendar, CalendarDate
    from datetime import datetime, timedelta
    
    calendar, _ = SupervisorCalendar.objects.get_or_create(
        supervisor=request.user
    )
    
    if request.method == "POST":
        # Parse dates
        date_str = request.POST.get('date')
        end_date_str = request.POST.get('end_date', '')
        time_str = request.POST.get('time', '')
        date_type = request.POST.get('date_type')
        is_bulk = request.POST.get('is_bulk') == 'on'
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            messages.error(request, "Invalid date format")
            return redirect("supervisor_calendar")
        
        # Parse time if provided
        time_obj = None
        if time_str:
            try:
                time_obj = datetime.strptime(time_str, '%H:%M').time()
            except:
                messages.error(request, "Invalid time format")
                return redirect("supervisor_calendar")
        
        # Get list of dates to create
        dates_to_create = [date_obj]
        
        if is_bulk and end_date_str:
            try:
                end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                if end_date_obj < date_obj:
                    messages.error(request, "End date must be after start date")
                    return redirect("supervisor_calendar")
                
                # Get selected days of week
                selected_days = request.POST.getlist('days_of_week')
                if not selected_days:
                    messages.error(request, "Please select at least one day of week for bulk creation")
                    return redirect("supervisor_calendar")
                
                selected_days = [int(d) for d in selected_days]
                
                # Generate dates for selected days
                current = date_obj
                dates_to_create = []
                while current <= end_date_obj:
                    if current.weekday() in selected_days:
                        dates_to_create.append(current)
                    current += timedelta(days=1)
                
                if not dates_to_create:
                    messages.error(request, "No dates match the selected criteria")
                    return redirect("supervisor_calendar")
            except:
                messages.error(request, "Invalid date range")
                return redirect("supervisor_calendar")
        
        # Process based on date type
        created_count = 0
        skipped_count = 0
        
        if date_type == 'session':
            school_id = request.POST.get('school')  # Gets value from hidden field
            scope = request.POST.get('scope', 'specific')  # 'all' or 'specific'
            class_ids = request.POST.getlist('class_section')
            
            if not school_id:
                messages.error(request, "Please select a school")
                return redirect("supervisor_calendar")
            
            try:
                school = School.objects.get(id=school_id)
            except:
                messages.error(request, "Invalid school selected")
                return redirect("supervisor_calendar")
            
            # Determine which classes to create entries for
            if scope == 'all':
                classes = list(ClassSection.objects.filter(school=school, is_active=True))
            else:
                if not class_ids:
                    messages.error(request, "Please select at least one class")
                    return redirect("supervisor_calendar")
                classes = list(ClassSection.objects.filter(id__in=class_ids, school=school, is_active=True))
            
            # Create a SINGLE CalendarDate entry for all grouped classes
            # Also create ONE shared 150-day PlannedSession for all grouped classes
            # Generate ONE grouped_session_id for all dates and classes
            import uuid as uuid_module
            grouped_session_id = uuid_module.uuid4()
            
            # Initialize grouped session plans ONCE for all classes
            # This creates the 150-day session plan with grouped_session_id
            if len(classes) > 1:
                # Multiple classes - create grouped session
                init_result = initialize_grouped_session_plans(classes, grouped_session_id)
                if not init_result['success']:
                    messages.error(request, f"Error initializing grouped session: {init_result['error']}")
                    return redirect("supervisor_calendar")
            else:
                # Single class - create individual session plan (no grouped_session_id)
                if len(classes) == 1:
                    from .session_management import SessionBulkManager
                    try:
                        # Delete any existing sessions for this class
                        PlannedSession.objects.filter(class_section=classes[0]).delete()
                        
                        # Create 150 individual sessions
                        sessions_to_create = []
                        for day_number in range(1, 151):
                            session = PlannedSession(
                                class_section=classes[0],
                                day_number=day_number,
                                title=f"Day {day_number} Session",
                                description=f"Session for day {day_number}",
                                sequence_position=day_number,
                                is_required=True,
                                is_active=True,
                                grouped_session_id=None  # No grouped_session_id for single class
                            )
                            sessions_to_create.append(session)
                        
                        PlannedSession.objects.bulk_create(sessions_to_create)
                    except Exception as e:
                        messages.error(request, f"Error creating session plan: {str(e)}")
                        return redirect("supervisor_calendar")
            
            for date_to_create in dates_to_create:
                # Check if entry already exists for this date and school
                existing = CalendarDate.objects.filter(
                    calendar=calendar,
                    date=date_to_create,
                    date_type=DateType.SESSION,
                    school=school
                ).first()
                
                if existing:
                    # Update existing entry with new classes
                    existing.class_sections.set(classes)
                    skipped_count += 1
                else:
                    # Create new entry
                    calendar_date = CalendarDate.objects.create(
                        calendar=calendar,
                        date=date_to_create,
                        time=time_obj,
                        date_type=DateType.SESSION,
                        school=school
                    )
                    # Add all selected classes to this single entry
                    calendar_date.class_sections.set(classes)
                    created_count += 1
        
        elif date_type == 'holiday':
            holiday_name = request.POST.get('holiday_name', '').strip()
            if not holiday_name:
                messages.error(request, "Please enter holiday name")
                return redirect("supervisor_calendar")
            
            # Create holiday entries (school-level, no class)
            for date_to_create in dates_to_create:
                existing = CalendarDate.objects.filter(
                    calendar=calendar,
                    date=date_to_create,
                    date_type=DateType.HOLIDAY
                ).exists()
                
                if existing:
                    skipped_count += 1
                    continue
                
                CalendarDate.objects.create(
                    calendar=calendar,
                    date=date_to_create,
                    time=time_obj,
                    date_type=DateType.HOLIDAY,
                    holiday_name=holiday_name
                )
                created_count += 1
        
        elif date_type == 'office_work':
            task_desc = request.POST.get('office_task_description', '').strip()
            school_id = request.POST.get('school')
            facilitator_ids = request.POST.getlist('facilitators')
            
            if not task_desc:
                messages.error(request, "Please enter office task description")
                return redirect("supervisor_calendar")
            
            try:
                school = School.objects.get(id=school_id) if school_id else None
            except:
                school = None
            
            # Create office work entries
            for date_to_create in dates_to_create:
                existing = CalendarDate.objects.filter(
                    calendar=calendar,
                    date=date_to_create,
                    date_type=DateType.OFFICE_WORK
                ).exists()
                
                if existing:
                    skipped_count += 1
                    continue
                
                calendar_date = CalendarDate.objects.create(
                    calendar=calendar,
                    date=date_to_create,
                    time=time_obj,
                    date_type=DateType.OFFICE_WORK,
                    office_task_description=task_desc,
                    school=school
                )
                
                # Add assigned facilitators
                if facilitator_ids:
                    facilitators = User.objects.filter(id__in=facilitator_ids, role__name__iexact="FACILITATOR")
                    calendar_date.assigned_facilitators.set(facilitators)
                
                created_count += 1
        
        # Show summary message
        if created_count > 0:
            msg = f"✅ Created {created_count} calendar entries"
            if skipped_count > 0:
                msg += f" ({skipped_count} skipped due to conflicts)"
            messages.success(request, msg)
        else:
            messages.warning(request, f"No entries created ({skipped_count} skipped due to conflicts)")
        
        return redirect("supervisor_calendar")
    
    # GET request - show form
    schools = School.objects.filter(status=1).order_by('name')
    classes = ClassSection.objects.filter(is_active=True).select_related('school').order_by('school__name', 'class_level', 'section')
    facilitators = User.objects.filter(role__name__iexact="FACILITATOR", is_active=True).order_by('full_name')
    
    context = {
        'schools': schools,
        'classes': classes,
        'facilitators': facilitators,
    }
    
    return render(request, "supervisor/calendar/add_date.html", context)


@login_required
@supervisor_required
def supervisor_calendar_edit_date(request, date_id):
    """Edit a calendar date entry"""
    from .models import CalendarDate, SupervisorCalendar
    
    calendar = SupervisorCalendar.objects.get(supervisor=request.user)
    calendar_date = get_object_or_404(CalendarDate, id=date_id, calendar=calendar)
    
    if request.method == "POST":
        date_type = request.POST.get('date_type')
        
        if date_type == 'session':
            class_ids = request.POST.getlist('class_section')
            if not class_ids:
                messages.error(request, "Please select at least one class")
            else:
                try:
                    classes = ClassSection.objects.filter(id__in=class_ids)
                    calendar_date.class_sections.set(classes)
                    calendar_date.date_type = DateType.SESSION
                    calendar_date.holiday_name = ''
                    calendar_date.office_task_description = ''
                    calendar_date.save()
                    messages.success(request, "Date updated successfully")
                except Exception as e:
                    messages.error(request, f"Error updating date: {str(e)}")
        
        elif date_type == 'holiday':
            holiday_name = request.POST.get('holiday_name', '').strip()
            if holiday_name:
                calendar_date.holiday_name = holiday_name
                calendar_date.date_type = DateType.HOLIDAY
                calendar_date.class_sections.clear()
                calendar_date.office_task_description = ''
                calendar_date.save()
                messages.success(request, "Date updated successfully")
            else:
                messages.error(request, "Please enter holiday name")
        
        elif date_type == 'office_work':
            task_desc = request.POST.get('office_task_description', '').strip()
            if task_desc:
                calendar_date.office_task_description = task_desc
                calendar_date.date_type = DateType.OFFICE_WORK
                calendar_date.class_sections.clear()
                calendar_date.holiday_name = ''
                calendar_date.save()
                messages.success(request, "Date updated successfully")
            else:
                messages.error(request, "Please enter office task description")
        
        return redirect("supervisor_calendar")
    
    classes = ClassSection.objects.filter(is_active=True).select_related('school').order_by('school__name', 'class_level', 'section')
    
    # Get selected class IDs for grouped sessions
    selected_class_ids = list(calendar_date.class_sections.values_list('id', flat=True)) if calendar_date.date_type == 'session' else []
    
    context = {
        'calendar_date': calendar_date,
        'classes': classes,
        'selected_class_ids': selected_class_ids,
    }
    
    return render(request, "supervisor/calendar/edit_date.html", context)


@login_required
@supervisor_required
def supervisor_calendar_delete_date(request, date_id):
    """Delete a calendar date entry"""
    from .models import CalendarDate, SupervisorCalendar
    
    calendar = SupervisorCalendar.objects.get(supervisor=request.user)
    calendar_date = get_object_or_404(CalendarDate, id=date_id, calendar=calendar)
    
    if request.method == "POST":
        date_str = str(calendar_date.date)
        calendar_date.delete()
        messages.success(request, f"Date entry for {date_str} deleted successfully")
        return redirect("supervisor_calendar")
    
    context = {
        'calendar_date': calendar_date,
    }
    
    return render(request, "supervisor/calendar/delete_confirm.html", context)


# =====================================================
# BULK STUDENT IMPORT FUNCTIONS
# =====================================================

@login_required
def supervisor_student_import(request, school_id):
    """Bulk import students via CSV/Excel for a specific school"""
    from django.http import HttpResponse
    import csv
    import openpyxl
    from datetime import date
    
    school = get_object_or_404(School, id=school_id)
    
    # Check if supervisor has access to this school
    if not request.user.role or request.user.role.name.upper() != "SUPERVISOR":
        messages.error(request, "Permission denied")
        return redirect("no_permission")
    
    class_sections = ClassSection.objects.filter(school=school)
    
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
            class_level = str(row.get("class_level", "")).strip()
            section = str(row.get("section", "")).strip()
            start_date = row.get("start_date") or date.today()
            
            # Validate
            if not all([enrollment_no, full_name, gender, class_level, section]):
                skipped_count += 1
                continue
            
            if gender.upper() not in ["M", "F"]:
                skipped_count += 1
                continue
            
            # Find class section
            class_section = ClassSection.objects.filter(
                school=school,
                class_level=class_level,
                section=section
            ).first()
            
            if not class_section:
                skipped_count += 1
                continue
            
            # Create student
            from .models import Student, Enrollment
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
                school=school,
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
        
        return redirect("supervisor_school_students", school_id=school_id)
    
    return render(request, "supervisor/students/import.html", {
        "school": school,
        "class_sections": class_sections
    })


@login_required
def supervisor_download_sample_csv(request):
    """Download sample CSV for student import"""
    from django.http import HttpResponse
    import csv
    
    sample_data = [
        ["enrollment_number", "full_name", "gender", "class_level", "section", "start_date"],
        ["E001", "John Doe", "M", "1", "A", "2026-01-12"],
        ["E002", "Jane Smith", "F", "1", "A", "2026-01-12"],
        ["E003", "Bob Johnson", "M", "2", "B", "2026-01-12"],
    ]
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students_sample.csv"'
    
    writer = csv.writer(response)
    for row in sample_data:
        writer.writerow(row)
    
    return response
