# Supervisor Views - Complete Management Interface
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q, Prefetch
from django.core.cache import cache
from .models import User, Role, School, ClassSection, FacilitatorSchool
from .forms import AddUserForm, EditUserForm, AddSchoolForm, ClassSectionForm, AssignFacilitatorForm

User = get_user_model()

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
    
    context = {
        'facilitator': facilitator,
        'schools': facilitator_schools,
        'classes': facilitator_classes,
        'students': facilitator_students,
        'recent_sessions': facilitator_sessions,
        'school_count': facilitator_schools.count(),
        'class_count': facilitator_classes.count(),
        'student_count': facilitator_students.count(),
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
