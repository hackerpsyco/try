import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Prefetch, Count, Q, Exists, OuterRef, Max
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers
import csv
import openpyxl
import os
import json
import logging
from .forms import AddUserForm, EditUserForm, AddSchoolForm, ClassSectionForm, AssignFacilitatorForm
from .models import User, Role, School, ClassSection, FacilitatorSchool,Student,Enrollment,PlannedSession,SessionStep, ActualSession, Attendance, CANCELLATION_REASONS
from .models import CurriculumSession, SessionTemplate, SessionUsageLog, ImportHistory, SessionVersionHistory
from .mixins import PerformanceOptimizedMixin, OptimizedListMixin, CachedViewMixin, AjaxOptimizedMixin, DatabaseOptimizedMixin, cache_expensive_operation, monitor_performance
from datetime import date
import re
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
import time

logger = logging.getLogger(__name__)
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

# Import the session management classes
from .session_management import SessionSequenceCalculator, SessionStatusManager

# -------------------------------
# Role-Based Dashboard Configuration
# -------------------------------
ROLE_CONFIG = {
    "ADMIN": {"url": "/admin/dashboard/", "template": "admin/dashboard.html"},
    "SUPERVISOR": {"url": "/supervisor/dashboard/", "template": "Supervisor/dashboard.html"},
    "FACILITATOR": {"url": "/facilitator/dashboard/", "template": "facilitator/dashboard.html"},
}

# -------------------------------
# Authentication Views
# -------------------------------
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)
            role_name = user.role.name.upper()
            redirect_url = ROLE_CONFIG.get(role_name, {}).get("url", "/")
            return redirect(redirect_url)

        messages.error(request, "Invalid email or password.")

    return render(request, "auth/login.html")


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect("login")


# -------------------------------
# Dashboard View
# -------------------------------
@login_required
def dashboard(request):
    role_name = request.user.role.name.upper()
    role_config = ROLE_CONFIG.get(role_name)

    if not role_config:
        messages.error(request, "Invalid role configuration or insufficient permissions.")
        return redirect("no_permission")

    context = {}
    if role_name == "ADMIN":
        context = {
            "users": User.objects.all().order_by("-created_at"),
            "roles": Role.objects.all(),
        }

    return render(request, role_config["template"], context)


# -------------------------------
# User Management Views
# -------------------------------
@login_required
def users_view(request):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to view this page.")
        return redirect("no_permission")

    users = User.objects.all().order_by("-created_at")
    roles = Role.objects.all()
    return render(request, "admin/users/users.html", {
        "users": users,
        "roles": roles
    })


@login_required
def add_user(request):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to add users.")
        return redirect("no_permission")

    if request.method == "POST":
        form = AddUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, "User created successfully!")
            return redirect("users_view")
    else:
        form = AddUserForm()

    return render(request, "admin/users/add_user.html", {"form": form})


@login_required
def edit_user(request, user_id):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to edit users.")
        return redirect("no_permission")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = EditUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully!")
            return redirect("users_view")
    else:
        form = EditUserForm(instance=user)

    return render(request, "admin/users/edit_user.html", {
        "form": form,
        "user": user
    })


@login_required
def delete_user(request, user_id):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to delete users.")
        return redirect("no_permission")

    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, "User deleted successfully!")
    return redirect("users_view")


# -------------------------------
# AJAX User Creation (NOT REMOVED)
# -------------------------------
@csrf_exempt
def create_user_ajax(request):
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
                role=role        # ✅ IMPORTANT — pass the Role object
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

# -------------------------------
# School Management Views
# -------------------------------
@login_required
@login_required
@monitor_performance
def schools(request):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to view schools.")
        return redirect("no_permission")

    # Optimized query with related data and statistics
    cache_key = f"schools_list_{request.user.id}"
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
        
        # Cache for 5 minutes
        cache.set(cache_key, schools, 300)
    
    form = AssignFacilitatorForm()
    return render(request, "admin/schools/list.html", {"schools": schools, "form": form})


@login_required
def add_school(request):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to add schools.")
        return redirect("no_permission")

    if request.method == "POST":
        form = AddSchoolForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "School added successfully!")
            return redirect("schools")
    else:
        form = AddSchoolForm()

    return render(request, "admin/schools/add_school.html", {"form": form})


@login_required
def edit_school(request, school_id):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to edit schools.")
        return redirect("no_permission")

    school = get_object_or_404(School, id=school_id)

    if request.method == "POST":
        form = AddSchoolForm(request.POST, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, "School updated successfully!")
            return redirect("schools")
    else:
        form = AddSchoolForm(instance=school)

    return render(request, "admin/schools/edit_school.html", {
        "form": form,
        "school": school
    })
@login_required
def delete_school(request, school_id):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to delete schools.")
        return redirect("no_permission")

    school = get_object_or_404(School, id=school_id)

    if request.method == "POST":
        school.delete()
        messages.success(request, "School deleted successfully!")
        return redirect("schools")

    messages.error(request, "Invalid request.")
    return redirect("schools")


@login_required
def school_detail(request, school_id):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to view school details.")
        return redirect("no_permission")

    school = get_object_or_404(School, id=school_id)
    classes = ClassSection.objects.filter(school=school).order_by("class_level", "section")
    
    # Get facilitator assignments for this school
    facilitator_assignments = FacilitatorSchool.objects.filter(
        school=school
    ).select_related("facilitator").order_by("-created_at")

    return render(request, "admin/schools/detail.html", {
        "school": school,
        "class_sections": classes,
        "facilitator_assignments": facilitator_assignments
    })


# -------------------------------
# Class Management Views
# -------------------------------
@login_required
def class_sections_list(request, school_id=None):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to view classes.")
        return redirect("no_permission")

    if school_id:
        school = get_object_or_404(School, id=school_id)
        class_sections = ClassSection.objects.filter(
            school=school
        ).order_by("class_level", "section")
    else:
        school = None
        class_sections = ClassSection.objects.all().order_by(
            "school__name", "class_level", "section"
        )

    return render(request, "admin/classes/list.html", {
        "school": school,
        "class_sections": class_sections,
        "schools": School.objects.all(),
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ClassSectionForm
from .models import School, ClassSection

@login_required
def class_section_add(request, school_id):
    # Permission check
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to add classes.")
        return redirect("no_permission")

    # Get the school
    school = get_object_or_404(School, id=school_id)

    if request.method == "POST":
        form = ClassSectionForm(request.POST)
        if form.is_valid():
            class_level = form.cleaned_data["class_level"]
            section = form.cleaned_data["section"]

            # Check duplicate
            if ClassSection.objects.filter(
                school=school,
                class_level=class_level,
                section=section
            ).exists():
                # Add non-field error to show in template
                form.add_error(None, f"Class {class_level} - {section} already exists for this school.")
            else:
                # Save new class section
                class_section = form.save(commit=False)
                class_section.school = school
                class_section.save()
                messages.success(request, "Class section added successfully!")
                return redirect("class_sections_list_by_school", school_id=school.id)
    else:
        form = ClassSectionForm()

    return render(request, "admin/classes/add.html", {
        "form": form,
        "school": school
    })


@login_required
def class_section_delete(request, pk):
    class_section = get_object_or_404(ClassSection, id=pk)
    school_id = class_section.school.id

    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to delete classes.")
        return redirect("no_permission")

    if request.method == "POST" or request.method == "GET":
        class_section.delete()
        messages.success(request, "Class section deleted successfully!")
        return redirect("class_sections_list_by_school", school_id=school_id)

@login_required
def class_view(request, school_id=None):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to view classes.")
        return redirect("no_permission")

    if school_id:
        return redirect("class_sections_list", school_id=school_id)

    return redirect("class_sections_list")


# -------------------------------
# No Permission
# -------------------------------
def no_permission(request):
    return render(request, "no_permission.html")
def edit_class_section(request, pk):
    class_section = get_object_or_404(ClassSection, id=pk)
    form = ClassSectionForm(request.POST or None, instance=class_section)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("class_sections_list")  # adjust as needed
    return render(request, "admin/classes/edit_class_section.html", {"form": form, "class_section": class_section})


def assign_facilitator(request):
    if request.method == "POST":
        form = AssignFacilitatorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Facilitator assigned successfully.")
            return redirect("assign-facilitator")
    else:
        form = AssignFacilitatorForm()

    return render(request, "admin/assign_facilitator.html", {
        "form": form
    })

def students_list(request, school_id):
    school = get_object_or_404(School, id=school_id)
    class_sections = ClassSection.objects.filter(school=school)

    class_section_id = request.GET.get("class_section")

    enrollments = Enrollment.objects.filter(
        school=school,
        is_active=True
    ).select_related("student", "class_section")

    if class_section_id:
        enrollments = enrollments.filter(class_section_id=class_section_id)

    return render(request, "admin/students/students_list.html", {
        "school": school,
        "class_sections": class_sections,
        "enrollments": enrollments,
        "selected_class_section": class_section_id,
    })


def student_add(request, school_id):
    school = get_object_or_404(School, id=school_id)
    class_sections = ClassSection.objects.filter(school=school)

    if request.method == "POST":
        student, _ = Student.objects.get_or_create(
            enrollment_number=request.POST["enrollment_number"],
            defaults={
                "full_name": request.POST["full_name"],
                "gender": request.POST["gender"]
            }
        )

        Enrollment.objects.get_or_create(
            student=student,
            school=school,
            class_section_id=request.POST["class_section"],
            defaults={
                "start_date": request.POST["start_date"],
                "is_active": True
            }
        )

        return redirect("students_list", school_id=school.id)

    return render(request, "admin/students/student_add.html", {
        "school": school,
        "class_sections": class_sections,
    })


def student_edit(request, school_id, student_id):
    school = get_object_or_404(School, id=school_id)
    student = get_object_or_404(Student, id=student_id)
    enrollment = get_object_or_404(
        Enrollment,
        student=student,
        school=school,
        is_active=True
    )
    class_sections = ClassSection.objects.filter(school=school)

    if request.method == "POST":
        student.enrollment_number = request.POST["enrollment_number"]
        student.full_name = request.POST["full_name"]
        student.gender = request.POST["gender"]
        student.save()

        enrollment.class_section_id = request.POST["class_section"]
        enrollment.start_date = request.POST["start_date"]
        enrollment.save()

        return redirect("students_list", school_id=school.id)

    return render(request, "admin/students/student_edit.html", {
        "school": school,
        "student": student,
        "enrollment": enrollment,
        "class_sections": class_sections,
    })

def student_delete(request, school_id, student_id):
    if request.method == "POST":
        enrollment = get_object_or_404(
            Enrollment,
            student_id=student_id,
            school_id=school_id,
            is_active=True
        )
        enrollment.is_active = False
        enrollment.save()

    return redirect("students_list", school_id=school_id)



def student_import(request, school_id):
    school = get_object_or_404(School, id=school_id)
    class_sections = ClassSection.objects.filter(school=school)

    if request.method == "POST":
        file = request.FILES.get("file")

        if not file:
            messages.error(request, "Please upload a file")
            return redirect(request.path)

        ext = file.name.split(".")[-1].lower()

        # ---------- READ FILE ----------
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
            messages.error(request, "Unsupported file format")
            return redirect(request.path)

        created_count = 0
        skipped_count = 0

        # ---------- PROCESS ROWS ----------
        for row in rows:
            enrollment_no = str(row.get("enrollment_number", "")).strip()
            full_name = str(row.get("full_name", "")).strip()
            gender = str(row.get("gender", "")).strip()
            class_level = str(row.get("class_level", "")).strip()
            section = str(row.get("section", "")).strip()
            start_date = row.get("start_date") or date.today()


            # Basic validation
            if not all([enrollment_no, full_name, gender, class_level, section]):
                skipped_count += 1
                continue

            class_section = ClassSection.objects.filter(
                school=school,
                class_level=class_level,
                section=section
            ).first()

            if not class_section:
                skipped_count += 1
                continue

            student, _ = Student.objects.get_or_create(
                enrollment_number=enrollment_no,
                defaults={
                    "full_name": full_name,
                    "gender": gender
                }
            )

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

        # ---------- USER FEEDBACK ----------
        if created_count == 0:
            messages.warning(
                request,
                f"No students imported. Skipped rows: {skipped_count}"
            )
        else:
            messages.success(
                request,
                f"{created_count} students imported successfully "
                f"(Skipped: {skipped_count})"
            )

        return redirect("students_list", school_id=school.id)

    return render(request, "admin/students/student_import.html", {
        "school": school,
        "class_sections": class_sections
    })


    
@login_required
def sessions_view(request, class_section_id):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    class_section = get_object_or_404(ClassSection, id=class_section_id)

    planned_sessions = (
        PlannedSession.objects
        .filter(class_section=class_section)
        .annotate(
            is_conducted=Exists(
                ActualSession.objects.filter(
                    planned_session=OuterRef("pk"),
                    status="conducted"
                )
            )
        )
        .prefetch_related("actual_sessions")
        .order_by("day_number")
    )

    for ps in planned_sessions:
        ps.status_info = "pending"
        ps.status_class = "secondary"

        if ps.is_conducted:
            ps.status_info = "completed"
            ps.status_class = "success"
        else:
            # ✅ get latest actual session ONLY
            last_actual = ps.actual_sessions.order_by("-date").first()

            if last_actual:
                if last_actual.status == "holiday":
                    ps.status_info = "holiday"
                    ps.status_class = "warning"
                elif last_actual.status == "cancelled":
                    ps.status_info = "cancelled"
                    ps.status_class = "danger"

    # ✅ first truly pending session
    next_pending = next(
        (ps for ps in planned_sessions if ps.status_info == "pending"),
        None
    )

    return render(request, "admin/classes/class_sessions.html", {
        "class_section": class_section,
        "planned_sessions": planned_sessions,
        "next_pending": next_pending,
    })
def extract_youtube_id(url):
    if not url:
        return None

    patterns = [
        r"youtu\.be\/([^?&]+)",
        r"youtube\.com\/watch\?v=([^?&]+)",
        r"youtube\.com\/shorts\/([^?&]+)",
        r"youtube\.com\/embed\/([^?&]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_curriculum_content_for_day(day_number):
    """Helper function to extract curriculum content for a specific day"""
    try:
        # Check cache first
        cache_key = f"curriculum_day_{day_number}"
        cached_content = cache.get(cache_key)
        if cached_content:
            return cached_content
        
        # Read the curriculum HTML file
        curriculum_file_path = os.path.join(settings.BASE_DIR, 'Templates/admin/session/English_ ALL DAYS.html')
        
        with open(curriculum_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Extract specific day content using regex
        day_pattern = rf'<td class="s0">\s*Day {day_number}\s*</td>'
        next_day_pattern = rf'<td class="s0">\s*Day {day_number + 1}\s*</td>'
        
        # Find start of current day
        day_match = re.search(day_pattern, content, re.IGNORECASE)
        if not day_match:
            return None
        
        start_pos = day_match.start()
        
        # Find start of next day (or end of content)
        next_day_match = re.search(next_day_pattern, content, re.IGNORECASE)
        if next_day_match:
            end_pos = next_day_match.start()
        else:
            # If it's the last day, find the end of table
            end_pos = content.find('</tbody>')
            if end_pos == -1:
                end_pos = len(content)
        
        # Extract day content
        day_content = content[start_pos:end_pos]
        
        # Cache the content for 1 hour
        cache.set(cache_key, day_content, 60 * 60)
        
        return day_content
        
    except Exception as e:
        print(f"Error loading curriculum content for day {day_number}: {e}")
        return None
@login_required
def today_session(request, class_section_id):
    if request.user.role.name.upper() != "FACILITATOR":
        return redirect("no_permission")

    class_section = get_object_or_404(ClassSection, id=class_section_id)
    today = timezone.now().date()

    # Use the new SessionSequenceCalculator
    from .session_management import SessionSequenceCalculator
    from .services.curriculum_content_resolver import CurriculumContentResolver
    from .services.session_integration_service import SessionIntegrationService
    
    # Check if class has any planned sessions, if not create them
    existing_sessions_count = PlannedSession.objects.filter(
        class_section=class_section,
        is_active=True
    ).count()
    
    if existing_sessions_count == 0:
        # Auto-generate 1-150 sessions for this class
        from .session_management import SessionBulkManager
        
        try:
            with transaction.atomic():
                # Create all 150 sessions
                sessions_to_create = []
                for day_number in range(1, 151):
                    session = PlannedSession(
                        class_section=class_section,
                        day_number=day_number,
                        title=f"Day {day_number} Session",
                        description=f"Session for day {day_number}",
                        sequence_position=day_number,
                        is_required=True,
                        is_active=True
                    )
                    sessions_to_create.append(session)
                
                # Bulk create all sessions
                PlannedSession.objects.bulk_create(sessions_to_create)
                
                messages.success(request, f"✅ Initialized 150 sessions for {class_section.school.name} - {class_section.class_level}-{class_section.section}")
                logger.info(f"Auto-generated 150 sessions for {class_section}")
            
        except Exception as e:
            logger.error(f"Error auto-generating sessions for {class_section}: {e}")
            messages.error(request, "Failed to initialize sessions. Please contact admin.")
            return render(request, "facilitator/Today_session.html", {
                "class_section": class_section,
                "error": True,
                "error_message": "Failed to initialize class sessions. Please contact admin."
            })
    
    # Get next pending session using the enhanced logic
    planned_session = SessionSequenceCalculator.get_next_pending_session(class_section)

    if not planned_session:
        # Check if we truly have all sessions completed
        total_sessions = PlannedSession.objects.filter(
            class_section=class_section,
            is_active=True
        ).count()
        
        completed_sessions = ActualSession.objects.filter(
            planned_session__class_section=class_section,
            status__in=['conducted', 'cancelled']
        ).count()
        
        if total_sessions > 0 and completed_sessions >= total_sessions:
            # All sessions truly completed - show completion message
            return render(request, "facilitator/Today_session.html", {
                "class_section": class_section,
                "completed": True,
                "completion_message": "🎉 All 150 sessions completed for this class!"
            })
        else:
            # Something is wrong with session sequence, try to repair
            from .session_management import SessionBulkManager
            repair_result = SessionBulkManager.repair_sequence_gaps(class_section, request.user)
            
            if repair_result['success'] and repair_result['created_count'] > 0:
                messages.info(request, f"Repaired {repair_result['created_count']} missing sessions.")
                # Try to get next session again
                planned_session = SessionSequenceCalculator.get_next_pending_session(class_section)
            
            if not planned_session:
                # Still no session found, show error
                return render(request, "facilitator/Today_session.html", {
                    "class_section": class_section,
                    "error": True,
                    "error_message": "No sessions available. Please contact admin to set up class sessions."
                })

    # Get latest actual session for this planned session
    actual_session = planned_session.actual_sessions.order_by("-date").first()

    session_status = "pending"
    is_today = False

    if actual_session:
        session_status = actual_session.status
        is_today = actual_session.date == today

    # Get first video from session steps (if any)
    first_step_with_video = planned_session.steps.filter(
        youtube_url__isnull=False
    ).exclude(youtube_url='').first()
    
    video_id = None
    if first_step_with_video:
        video_id = extract_youtube_id(first_step_with_video.youtube_url)
    
    # Initialize our new services
    content_resolver = CurriculumContentResolver()
    integration_service = SessionIntegrationService()
    
    # Get integrated session data (combines PlannedSession with CurriculumSession)
    integrated_data = integration_service.get_integrated_session_data(planned_session)
    
    # Log curriculum access for analytics
    integration_service.log_curriculum_access(planned_session, request.user, request)
    
    # Get curriculum content metadata for the frontend
    content_metadata = content_resolver.get_content_metadata(
        planned_session.day_number, 
        integration_service._get_class_language(class_section)
    )
    
    # Get progress metrics
    progress_metrics = SessionSequenceCalculator.calculate_progress(class_section)
    
    # Get workflow-related data
    from .models import LessonPlanUpload, SessionReward, SessionFeedback, SessionPreparationChecklist
    
    # Get lesson plan uploads for this session
    lesson_plan_uploads = LessonPlanUpload.objects.filter(
        planned_session=planned_session,
        facilitator=request.user
    ).order_by('-upload_date')
    
    # Get session rewards for this session (if actual session exists)
    session_rewards = []
    if actual_session:
        session_rewards = SessionReward.objects.filter(
            actual_session=actual_session
        ).order_by('-reward_date')
    
    # Get preparation checklist for this session
    preparation_checklist = SessionPreparationChecklist.objects.filter(
        planned_session=planned_session,
        facilitator=request.user
    ).first()
    
    if not preparation_checklist:
        # Create empty checklist for template
        preparation_checklist = SessionPreparationChecklist(
            planned_session=planned_session,
            facilitator=request.user
        )

    return render(request, "facilitator/Today_session.html", {
        "class_section": class_section,
        "planned_session": planned_session,
        "actual_session": actual_session,
        "session_status": session_status,
        "is_today": is_today,
        "video_id": video_id,
        "current_day": planned_session.day_number,
        "progress_metrics": progress_metrics,
        "cancellation_reasons": CANCELLATION_REASONS,
        "lesson_plan_uploads": lesson_plan_uploads,
        "session_rewards": session_rewards,
        "preparation_checklist": preparation_checklist,
        # New curriculum integration data
        "integrated_data": integrated_data,
        "content_metadata": content_metadata,
        "has_admin_content": integrated_data.has_admin_content,
        "content_source": integrated_data.content_source,
        # Day navigation data
        "day_range": range(1, 151),  # Days 1-150
        # Debug information
        "today_date": today,
        "actual_session_date": actual_session.date if actual_session else None,
    })




@login_required
def debug_sessions(request, class_section_id):
    """Debug view to show all sessions and their status"""
    class_section = get_object_or_404(ClassSection, id=class_section_id)
    
    # Get all planned sessions
    all_sessions = PlannedSession.objects.filter(
        class_section=class_section,
        is_active=True
    ).order_by("day_number")
    
    session_info = []
    for session in all_sessions:
        if session.actual_sessions.exists():
            actual = session.actual_sessions.first()
            status = f"{actual.status} on {actual.date}"
        else:
            status = "PENDING (not processed)"
        
        session_info.append({
            'day': session.day_number,
            'topic': session.topic,
            'status': status
        })
    
    return render(request, "facilitator/debug_sessions.html", {
        "class_section": class_section,
        "session_info": session_info,
    })

from django.utils import timezone

@login_required
def start_session(request, planned_session_id):
    if request.user.role.name.upper() != "FACILITATOR":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    planned = get_object_or_404(PlannedSession, id=planned_session_id)
    status = request.POST.get("status", "conducted")
    remarks = request.POST.get("remarks", "")
    cancellation_reason = request.POST.get("cancellation_reason", "")

    # Import the new session management logic
    from .session_management import SessionStatusManager
    from django.core.exceptions import ValidationError

    try:
        if status == "conducted":
            actual_session = SessionStatusManager.conduct_session(
                planned_session=planned,
                facilitator=request.user,
                remarks=remarks
            )
            messages.success(request, "Session conducted successfully!")
            return redirect("mark_attendance", actual_session.id)
            
        elif status == "holiday":
            actual_session = SessionStatusManager.mark_holiday(
                planned_session=planned,
                facilitator=request.user,
                reason=remarks
            )
            messages.success(request, "Session marked as holiday. You can conduct it later.")
            
        elif status == "cancelled":
            if not cancellation_reason:
                messages.error(request, "Please select a cancellation reason.")
                return redirect("facilitator_today_session", class_section_id=planned.class_section.id)
            
            actual_session = SessionStatusManager.cancel_session(
                planned_session=planned,
                facilitator=request.user,
                cancellation_reason=cancellation_reason,
                remarks=remarks
            )
            messages.success(request, f"Session cancelled permanently: {dict(CANCELLATION_REASONS)[cancellation_reason]}")
        
        else:
            messages.error(request, "Invalid session status.")
            return redirect("facilitator_today_session", class_section_id=planned.class_section.id)
            
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect("facilitator_today_session", class_section_id=planned.class_section.id)
    except Exception as e:
        messages.error(request, f"Error processing session: {str(e)}")
        return redirect("facilitator_today_session", class_section_id=planned.class_section.id)

    return redirect("facilitator_today_session", class_section_id=planned.class_section.id)

@login_required
def mark_attendance(request, actual_session_id):
    if request.user.role.name.upper() != "FACILITATOR":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")
    
    session = get_object_or_404(ActualSession, id=actual_session_id)

    if session.status != "conducted":
        messages.error(request, "Cannot mark attendance — session is not conducted.")
        return redirect("facilitator_classes")

    enrollments = Enrollment.objects.filter(
        class_section=session.planned_session.class_section,
        is_active=True
    ).select_related("student").prefetch_related(
        Prefetch(
            'attendances',
            queryset=Attendance.objects.filter(actual_session=session),
            to_attr='session_attendances'
        )
    )

    if request.method == "POST":
        saved_count = 0
        skipped_count = 0
        updated_count = 0
        
        try:
            with transaction.atomic():
                for enrollment in enrollments:
                    status = request.POST.get(str(enrollment.id))
                    
                    # Only save if a status is selected (not empty/not marked)
                    if status and status in ['present', 'absent', 'leave']:
                        attendance, created = Attendance.objects.update_or_create(
                            actual_session=session,
                            enrollment=enrollment,
                            defaults={"status": status}
                        )
                        
                        if created:
                            saved_count += 1
                        else:
                            updated_count += 1
                    else:
                        # If status is empty, delete existing attendance if any
                        Attendance.objects.filter(
                            actual_session=session,
                            enrollment=enrollment
                        ).delete()
                        skipped_count += 1

                # Update session attendance_marked flag
                session.attendance_marked = True
                session.save()

                # Create success message with details
                message_parts = []
                if saved_count > 0:
                    message_parts.append(f"{saved_count} new attendance records saved")
                if updated_count > 0:
                    message_parts.append(f"{updated_count} attendance records updated")
                if skipped_count > 0:
                    message_parts.append(f"{skipped_count} students not marked")
                
                success_message = "Attendance saved successfully! " + ", ".join(message_parts) + "."
                messages.success(request, success_message)
                
                return redirect("facilitator_today_session", class_section_id=session.planned_session.class_section.id)
                
        except Exception as e:
            messages.error(request, f"Error saving attendance: {str(e)}")
            logger.error(f"Error saving attendance for session {session.id}: {e}")

    # For GET request, get existing attendance data
    for enrollment in enrollments:
        # Get existing attendance for this enrollment in this session
        existing_attendance = Attendance.objects.filter(
            actual_session=session,
            enrollment=enrollment
        ).first()
        enrollment.existing_attendance = existing_attendance

    return render(request, "facilitator/mark_attendance.html", {
        "session": session,
        "enrollments": enrollments
    })


@login_required
def class_attendance(request, class_section_id):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    class_section = get_object_or_404(ClassSection, id=class_section_id)

    sessions = ActualSession.objects.filter(
        planned_session__class_section=class_section
    ).select_related("planned_session").order_by("-date")

    return render(request, "admin/classes/class_attendance.html", {
        "class_section": class_section,
        "sessions": sessions
    })


@login_required
def facilitator_classes(request):
    if request.user.role.name.upper() != "FACILITATOR":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    # Schools assigned to facilitator
    assigned_schools = FacilitatorSchool.objects.filter(
        facilitator=request.user
    ).select_related("school")

    # All classes from those schools
    class_sections = ClassSection.objects.filter(
        school__in=[fs.school for fs in assigned_schools]
    ).order_by("school__name", "class_level", "section")

    return render(request, "facilitator/classes/list.html", {
        "class_sections": class_sections
    })


@login_required
def facilitator_attendance(request):
    """Enhanced attendance filtering interface for facilitators"""
    if request.user.role.name.upper() != "FACILITATOR":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    # Get facilitator's assigned schools
    assigned_schools = FacilitatorSchool.objects.filter(
        facilitator=request.user,
        is_active=True
    ).select_related("school")

    # Check if facilitator has any school assignments
    if not assigned_schools.exists():
        messages.warning(request, f"No active schools assigned to facilitator {request.user.full_name}. Please contact admin to assign schools.")

    context = {
        "assigned_schools": assigned_schools,
    }

    # If filters are applied, get the filtered data
    school_id = request.GET.get("school")
    class_section_id = request.GET.get("class_section")
    
    if school_id:
        # Verify facilitator has access to this school
        if not assigned_schools.filter(school_id=school_id).exists():
            messages.error(request, "You don't have access to this school.")
            return redirect("facilitator_attendance")
        
        school = get_object_or_404(School, id=school_id)
        context["selected_school"] = school
        
        # Get classes for this school
        class_sections = ClassSection.objects.filter(
            school=school,
            is_active=True
        ).order_by("class_level", "section")
        context["class_sections"] = class_sections
        
        if class_section_id:
            # Verify class belongs to selected school
            if not class_sections.filter(id=class_section_id).exists():
                messages.error(request, "Invalid class selection.")
                return redirect("facilitator_attendance")
            
            class_section = get_object_or_404(ClassSection, id=class_section_id)
            context["selected_class_section"] = class_section
            
            # Get students for this class with attendance summary
            enrollments = Enrollment.objects.filter(
                class_section=class_section,
                is_active=True
            ).select_related("student").order_by("student__full_name")
            
            # Calculate attendance statistics for each student
            enrollment_stats = []
            for enrollment in enrollments:
                # Count total conducted sessions for this class
                total_sessions = ActualSession.objects.filter(
                    planned_session__class_section=class_section,
                    status="conducted"
                ).count()
                
                # Count attendance records for this student
                present_count = Attendance.objects.filter(
                    enrollment=enrollment,
                    actual_session__planned_session__class_section=class_section,
                    status="present"
                ).count()
                
                absent_count = Attendance.objects.filter(
                    enrollment=enrollment,
                    actual_session__planned_session__class_section=class_section,
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
            
            context["enrollment_stats"] = enrollment_stats
            
            # Get recent attendance sessions for this class with detailed attendance
            recent_sessions_data = []
            recent_sessions = ActualSession.objects.filter(
                planned_session__class_section=class_section,
                status="conducted"
            ).select_related("planned_session").order_by("-date")[:10]
            
            for session in recent_sessions:
                present_count = session.attendances.filter(status="present").count()
                absent_count = session.attendances.filter(status="absent").count()
                total_count = session.attendances.count()
                
                recent_sessions_data.append({
                    'session': session,
                    'present_count': present_count,
                    'absent_count': absent_count,
                    'total_count': total_count
                })
            
            context["recent_sessions_data"] = recent_sessions_data

    return render(request, "facilitator/attendance_filter.html", context)

@login_required
def admin_attendance_filter(request):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    context = {}

    # Schools dropdown
    context["schools"] = School.objects.all().order_by("name")

    # 🔹 Preload ALL classes (needed for fast dropdown)
    classes_by_school = ClassSection.objects.values(
        "id", "class_level", "section", "school_id"
    )
    context["classes_json"] = json.dumps(list(classes_by_school), cls=DjangoJSONEncoder)

    school_id = request.GET.get("school")
    class_section_id = request.GET.get("class_section")

    if school_id:
        school = get_object_or_404(School, id=school_id)
        context["selected_school"] = school

        if class_section_id:
            class_section = get_object_or_404(ClassSection, id=class_section_id)
            context["selected_class_section"] = class_section

            enrollments = Enrollment.objects.filter(
                class_section=class_section,
                is_active=True
            ).select_related("student").order_by("student__full_name")

            total_sessions = ActualSession.objects.filter(
                planned_session__class_section=class_section,
                status="conducted"
            ).count()

            stats = []
            for e in enrollments:
                present = Attendance.objects.filter(enrollment=e, status="present").count()
                absent = Attendance.objects.filter(enrollment=e, status="absent").count()
                percent = (present / total_sessions * 100) if total_sessions else 0

                stats.append({
                    "enrollment": e,
                    "present": present,
                    "absent": absent,
                    "total": total_sessions,
                    "percent": round(percent, 1),
                })

            context["enrollment_stats"] = stats

            context["recent_sessions"] = ActualSession.objects.filter(
                planned_session__class_section=class_section,
                status="conducted"
            ).select_related("planned_session").order_by("-date")[:10]

    return render(request, "admin/attendance_filter.html", context)

# AJAX endpoints for cascading filters
@login_required
def ajax_facilitator_schools(request):
    """AJAX endpoint to get schools assigned to facilitator"""
    if request.user.role.name.upper() != "FACILITATOR":
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    schools = FacilitatorSchool.objects.filter(
        facilitator=request.user,
        is_active=True
    ).select_related("school").values(
        "school__id", "school__name", "school__district"
    )
    
    return JsonResponse({
        "schools": list(schools)
    })


@login_required
def ajax_school_classes(request):
    """AJAX endpoint to get classes for a specific school"""
    if request.user.role.name.upper() != "FACILITATOR":
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    school_id = request.GET.get("school_id")
    if not school_id:
        return JsonResponse({"error": "School ID required"}, status=400)
    
    # Verify facilitator has access to this school
    if not FacilitatorSchool.objects.filter(
        facilitator=request.user,
        school_id=school_id,
        is_active=True
    ).exists():
        return JsonResponse({"error": "Access denied to this school"}, status=403)
    
    classes = ClassSection.objects.filter(
        school_id=school_id,
        is_active=True
    ).values(
        "id", "class_level", "section"
    ).order_by("class_level", "section")
    
    return JsonResponse({
        "classes": list(classes)
    })


@login_required
def ajax_class_students(request):
    """AJAX endpoint to get students for a specific class"""
    if request.user.role.name.upper() != "FACILITATOR":
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    class_section_id = request.GET.get("class_section_id")
    if not class_section_id:
        return JsonResponse({"error": "Class section ID required"}, status=400)
    
    # Verify facilitator has access to this class through school assignment
    class_section = get_object_or_404(ClassSection, id=class_section_id)
    if not FacilitatorSchool.objects.filter(
        facilitator=request.user,
        school=class_section.school,
        is_active=True
    ).exists():
        return JsonResponse({"error": "Access denied to this class"}, status=403)
    
    students = Enrollment.objects.filter(
        class_section_id=class_section_id,
        is_active=True
    ).select_related("student").values(
        "id", "student__id", "student__full_name", "student__enrollment_number"
    ).order_by("student__full_name")
    
    return JsonResponse({
        "students": list(students)
    })
@login_required
def planned_session_create(request, class_section_id):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    class_section = get_object_or_404(ClassSection, id=class_section_id)

    if request.method == "POST":
        topic = request.POST.get("topic")
        youtube_url = request.POST.get("youtube_url")
        description = request.POST.get("description", "")

        last_day = PlannedSession.objects.filter(
            class_section=class_section
        ).aggregate(Max("day_number"))["day_number__max"] or 0

        PlannedSession.objects.create(
            class_section=class_section,
            day_number=last_day + 1,
            topic=topic,
            youtube_url=youtube_url,
            description=description
        )

        messages.success(request, "Planned session added.")
        return redirect("admin_class_sessions", class_section.id)

    return render(request, "admin/classes/planned_session_form.html", {
        "class_section": class_section
    })

@login_required
def planned_session_edit(request, session_id):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    planned = get_object_or_404(PlannedSession, id=session_id)
    class_section = planned.class_section

    if request.method == "POST":
        planned.topic = request.POST.get("topic")
        planned.youtube_url = request.POST.get("youtube_url")
        planned.description = request.POST.get("description", "")
        planned.save()

        messages.success(request, "Planned session updated.")
        return redirect("admin_class_sessions", class_section.id)

    return render(request, "admin/classes/planned_session_form.html", {
        "class_section": class_section,
        "planned_session": planned,
        "is_edit": True
    })
@login_required
def planned_session_delete(request, session_id):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    planned = get_object_or_404(PlannedSession, id=session_id)
    class_section = planned.class_section

    # Handle both GET and POST requests for deletion
    if request.method == "POST" or request.method == "GET":
        # Get related data count for user feedback
        actual_sessions_count = planned.actual_sessions.count()
        attendance_count = 0
        
        if actual_sessions_count > 0:
            # Count attendance records that will be deleted
            for actual_session in planned.actual_sessions.all():
                attendance_count += actual_session.attendances.count()
        
        # Delete the planned session (this will cascade delete ActualSession and Attendance records)
        planned.delete()
        
        # Provide detailed feedback about what was deleted
        if actual_sessions_count > 0:
            messages.success(
                request, 
                f"Planned session deleted successfully. Also deleted {actual_sessions_count} actual session(s) and {attendance_count} attendance record(s)."
            )
        else:
            messages.success(request, "Planned session deleted successfully.")
            
        return redirect("admin_class_sessions", class_section.id)

    # Optional confirm page (if needed in future)
    return render(request, "admin/classes/planned_session_confirm_delete.html", {
        "planned_session": planned,
        "class_section": class_section,
    })

@login_required
def planned_session_import(request, class_section_id):

    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    class_section = get_object_or_404(ClassSection, id=class_section_id)

    if request.method == "POST":
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "Upload CSV file.")
            return redirect(request.path)

        content = file.read().decode("utf-8", errors="ignore")
        reader = csv.reader(content.splitlines())

        current_day = None
        current_session = None
        current_step = None
        order = 1

        for row in reader:
            if not any(row):
                continue

            cell_a = row[0].strip() if len(row) > 0 else ""
            cell_b = row[1].strip() if len(row) > 1 else ""
            cell_c = row[2].strip() if len(row) > 2 else ""
            cell_d = row[3].strip() if len(row) > 3 else ""

            # -----------------------------
            # DAY HEADER (Day 1, Day 2)
            # -----------------------------
            if cell_a.lower().startswith("day"):
                day_number = int(cell_a.replace("Day", "").strip())

                current_session, _ = PlannedSession.objects.get_or_create(
                    class_section=class_section,
                    day_number=day_number,
                    defaults={
                        "title": f"Day {day_number}",
                        "description": "",
                        "is_active": True,
                    }
                )

                SessionStep.objects.filter(
                    planned_session=current_session
                ).delete()

                current_step = None
                order = 1
                continue

            # -----------------------------
            # HEADER ROW (When / What)
            # -----------------------------
            if cell_a.lower() == "when":
                continue

            # -----------------------------
            # NEW STEP ROW
            # -----------------------------
            if cell_a:
                current_step = SessionStep.objects.create(
                    planned_session=current_session,
                    order=order,
                    subject=map_subject(cell_b),
                    title=cell_b,
                    description=cell_d,
                    duration_minutes=parse_minutes(cell_c),
                )
                order += 1
                continue

            # -----------------------------
            # CONTINUATION ROW (DETAILS)
            # -----------------------------
            if current_step and cell_d:
                current_step.description += "\n" + cell_d
                current_step.save()

        messages.success(request, "Curriculum imported successfully ✔")
        return redirect("admin_class_sessions", class_section.id)

    return render(request, "admin/classes/planned_session_import.html", {
        "class_section": class_section
    })
def parse_minutes(text):
    if not text:
        return None
    try:
        return int(text.split()[0])
    except:
        return None


def map_subject(title):
    t = title.lower()
    if "hindi" in t:
        return "hindi"
    if "english" in t:
        return "english"
    if "math" in t:
        return "maths"
    if "computer" in t:
        return "computer"
    if "mindfulness" in t:
        return "mindfulness"
    return "activity"



@login_required
def bulk_delete_sessions(request, class_section_id):
    """Bulk delete planned sessions"""
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    class_section = get_object_or_404(ClassSection, id=class_section_id)

    if request.method == "POST":
        session_ids = request.POST.getlist('session_ids')
        
        if not session_ids:
            messages.error(request, "No sessions selected for deletion.")
            return redirect("admin_class_sessions", class_section.id)

        # Get sessions to delete
        sessions_to_delete = PlannedSession.objects.filter(
            id__in=session_ids,
            class_section=class_section
        )

        if not sessions_to_delete.exists():
            messages.error(request, "No valid sessions found for deletion.")
            return redirect("admin_class_sessions", class_section.id)

        # Count related data that will be deleted
        total_actual_sessions = 0
        total_attendance = 0
        
        for session in sessions_to_delete:
            actual_sessions_count = session.actual_sessions.count()
            total_actual_sessions += actual_sessions_count
            
            for actual_session in session.actual_sessions.all():
                total_attendance += actual_session.attendances.count()

        # Delete all selected sessions
        deleted_count = sessions_to_delete.count()
        sessions_to_delete.delete()

        # Provide detailed feedback
        message = f"Successfully deleted {deleted_count} planned session(s)."
        if total_actual_sessions > 0:
            message += f" Also deleted {total_actual_sessions} actual session(s) and {total_attendance} attendance record(s)."
        
        messages.success(request, message)

    return redirect("admin_class_sessions", class_section.id)


@login_required
def download_sample_csv(request):
    """Download a sample CSV file for planned sessions import"""
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    # Create sample CSV content
    sample_data = [
        ["topic", "day_number", "youtube_url", "description"],
        ["Introduction to Math", "1", "https://youtube.com/watch?v=abc123", "Basic math concepts"],
        ["Addition and Subtraction", "2", "https://youtube.com/watch?v=def456", "Learning basic operations"],
        ["Multiplication Tables", "3", "", "Practice multiplication"],
        ["Division Basics", "", "https://youtube.com/watch?v=ghi789", "Understanding division"]
    ]

    # Create HTTP response with CSV content
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="planned_sessions_sample.csv"'

    writer = csv.writer(response)
    for row in sample_data:
        writer.writerow(row)

    return response


@login_required
def toggle_facilitator_assignment(request, assignment_id):
    """Toggle facilitator assignment active status"""
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    assignment = get_object_or_404(FacilitatorSchool, id=assignment_id)
    
    if request.method == "POST":
        new_status = request.POST.get('is_active') == 'true'
        assignment.is_active = new_status
        assignment.save()
        
        status_text = "activated" if new_status else "deactivated"
        messages.success(request, f"Facilitator assignment {status_text} successfully.")
    
    return redirect("school_detail", school_id=assignment.school.id)


@login_required
def delete_facilitator_assignment(request, assignment_id):
    """Delete facilitator assignment"""
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    assignment = get_object_or_404(FacilitatorSchool, id=assignment_id)
    school_id = assignment.school.id
    
    if request.method == "POST":
        facilitator_name = assignment.facilitator.full_name
        assignment.delete()
        messages.success(request, f"Facilitator {facilitator_name} removed from school successfully.")
    
    return redirect("school_detail", school_id=school_id)


@login_required
def admin_sessions_filter(request):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    # Clear cache to ensure fresh data
    from django.core.cache import cache
    cache.clear()

    schools = School.objects.all()
    classes = ClassSection.objects.none()

    school_id = request.GET.get("school")
    class_id = request.GET.get("class")

    # when school selected → load related classes
    if school_id:
        classes = ClassSection.objects.filter(school_id=school_id)

    # when both selected → redirect
    if school_id and class_id:
        return redirect("admin_class_sessions", class_section_id=class_id)

    # Get curriculum session statistics for the template
    hindi_sessions = CurriculumSession.objects.filter(language='hindi').count()
    english_sessions = CurriculumSession.objects.filter(language='english').count()

    # Get recent activity from both systems
    recent_class_sessions = ActualSession.objects.select_related(
        'planned_session', 'facilitator', 'planned_session__class_section__school'
    ).order_by('-created_at')[:5]

    recent_curriculum_updates = CurriculumSession.objects.select_related(
        'created_by'
    ).order_by('-updated_at')[:5]

    return render(request, "admin/sessions/filter.html", {
        "schools": schools,
        "classes": classes,
        "hindi_sessions": hindi_sessions,
        "english_sessions": english_sessions,
        "recent_class_sessions": recent_class_sessions,
        "recent_curriculum_updates": recent_curriculum_updates,
        "debug_template": "admin/sessions/filter.html",  # Debug info
        "user_role": request.user.role.name.upper(),  # Debug info
    })




from django.utils import timezone
from django.contrib import messages

@login_required
def dashboard(request):
    role_name = request.user.role.name.upper()
    role_config = ROLE_CONFIG.get(role_name)

    if not role_config:
        messages.error(request, "Invalid role.")
        return redirect("no_permission")

    context = {}

    if role_name == "ADMIN":
        today = timezone.now().date()

        # ===== TOP STATS =====
        context["active_schools"] = School.objects.filter(status=1).count()

        context["active_facilitators"] = User.objects.filter(
            role__name__iexact="FACILITATOR",
            is_active=True
        ).count()

        context["enrolled_students"] = Enrollment.objects.filter(
            is_active=True
        ).count()

        context["pending_validations"] = PlannedSession.objects.filter(
            is_active=True
        ).exclude(
            actual_sessions__status="conducted"
        ).count()

        # ===== SYSTEM SNAPSHOT (TODAY) =====
        context["sessions_today"] = ActualSession.objects.filter(
            date=today,
            status="conducted"
        ).count()

        context["holidays_today"] = ActualSession.objects.filter(
            date=today,
            status="holiday"
        ).count()

        context["cancelled_today"] = ActualSession.objects.filter(
            date=today,
            status="cancelled"
        ).count()

        # ===== RECENT ACTIVITY =====
        context["recent_activities"] = ActualSession.objects.select_related(
            "facilitator",
            "planned_session",
            "planned_session__class_section",
            "planned_session__class_section__school"
        ).order_by("-created_at")[:10]

        # For Create User Modal
        context["roles"] = Role.objects.all()

    return render(request, role_config["template"], context)

@login_required
def curriculum_navigator(request):
    """View to display the interactive curriculum day navigator"""
    if request.user.role.name.upper() not in ["ADMIN", "FACILITATOR"]:
        messages.error(request, "You do not have permission to view the curriculum.")
        return redirect("no_permission")
    
    return render(request, "admin/session/English_ ALL DAYS.html")


@login_required
def hindi_curriculum_navigator(request):
    """View to display the interactive Hindi curriculum day navigator"""
    if request.user.role.name.upper() not in ["ADMIN", "FACILITATOR"]:
        messages.error(request, "You do not have permission to view the curriculum.")
        return redirect("no_permission")
    
    return render(request, "admin/session/Hindi_Interactive.html")


@login_required
def facilitator_curriculum_session(request, class_section_id):
    """Enhanced facilitator session view with integrated curriculum navigator"""
    if request.user.role.name.upper() != "FACILITATOR":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    class_section = get_object_or_404(ClassSection, id=class_section_id)
    
    # Verify facilitator has access to this class
    if not FacilitatorSchool.objects.filter(
        facilitator=request.user,
        school=class_section.school,
        is_active=True
    ).exists():
        messages.error(request, "You don't have access to this class.")
        return redirect("facilitator_classes")

    # Get requested day or current pending day
    requested_day = request.GET.get('day')
    if requested_day:
        try:
            current_day_number = int(requested_day)
        except ValueError:
            current_day_number = 1
    else:
        # Get next pending session
        next_session = (
            PlannedSession.objects
            .filter(class_section=class_section, is_active=True)
            .exclude(actual_sessions__status="conducted")
            .order_by("day_number")
            .first()
        )
        current_day_number = next_session.day_number if next_session else 1

    # Get planned session for current day
    planned_session = PlannedSession.objects.filter(
        class_section=class_section,
        day_number=current_day_number,
        is_active=True
    ).first()

    # Get actual session status
    actual_session = None
    session_status = "pending"
    
    if planned_session:
        actual_session = planned_session.actual_sessions.order_by("-date").first()
        if actual_session:
            session_status = actual_session.status

    # Get session statuses for all days (for navigator)
    all_sessions = PlannedSession.objects.filter(
        class_section=class_section,
        is_active=True
    ).prefetch_related('actual_sessions')
    
    session_statuses = {}
    for session in all_sessions:
        latest_actual = session.actual_sessions.order_by("-date").first()
        if latest_actual:
            session_statuses[session.day_number] = latest_actual.status
        else:
            session_statuses[session.day_number] = "pending"

    # Navigation helpers
    prev_day = current_day_number - 1 if current_day_number > 1 else None
    next_day = current_day_number + 1 if current_day_number < 150 else None

    context = {
        'class_section': class_section,
        'planned_session': planned_session,
        'actual_session': actual_session,
        'session_status': session_status,
        'current_day_number': current_day_number,
        'prev_day': prev_day,
        'next_day': next_day,
        'session_statuses': json.dumps(session_statuses),
    }

    return render(request, "facilitator/curriculum_session.html", context)


@login_required
def curriculum_content_api(request):
    """Enhanced API endpoint to serve curriculum content using CurriculumContentResolver"""
    if request.user.role.name.upper() not in ["ADMIN", "FACILITATOR"]:
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    day = request.GET.get('day', 1)
    language = request.GET.get('language', 'english').lower()
    class_section_id = request.GET.get('class_section_id')
    
    try:
        day = int(day)
    except ValueError:
        day = 1
    
    # Validate language
    if language not in ['english', 'hindi']:
        language = 'english'
    
    # Get class section if provided (for better language detection)
    class_section = None
    if class_section_id:
        try:
            class_section = ClassSection.objects.get(id=class_section_id)
        except ClassSection.DoesNotExist:
            pass
    
    # Use our new CurriculumContentResolver
    from .services.curriculum_content_resolver import CurriculumContentResolver
    from .services.session_integration_service import SessionIntegrationService
    
    content_resolver = CurriculumContentResolver()
    integration_service = SessionIntegrationService()
    
    try:
        # Resolve content using our new service
        content_result = content_resolver.resolve_content(day, language, class_section)
        
        # Get content metadata
        metadata = content_resolver.get_content_metadata(day, language)
        
        # Create enhanced response with source indicators
        source_badge = {
            'admin_managed': '<span class="badge bg-success">Admin Managed</span>',
            'static_fallback': '<span class="badge bg-warning">Static Content</span>',
            'error_fallback': '<span class="badge bg-danger">Error</span>'
        }.get(content_result.source, '<span class="badge bg-secondary">Unknown</span>')
        
        # Return content directly since _extract_day_content already provides proper wrapper
        # Return content directly since _extract_day_content already provides proper wrapper
        wrapped_content = f'''
        <div class="api-content-wrapper" data-day="{day}" data-language="{language}" data-source="{content_result.source}">
            {_format_content_with_source_info(content_result, metadata)}
            
            <div class="content-body">
                {content_result.content}
            </div>
            
            {_add_admin_management_links(content_result, day, language, request.user)}
        </div>
        '''
        
        return HttpResponse(wrapped_content)
        
    except Exception as e:
        logger.error(f"Error in curriculum_content_api: {str(e)}")
        error_content = f'''
        <div class="alert alert-danger m-3">
            <h6>Error Loading Content</h6>
            <p>Failed to load Day {day} {language.title()} curriculum content.</p>
            <small class="text-muted">Error: {str(e)}</small>
            <button class="btn btn-outline-danger btn-sm mt-2" onclick="loadCurriculumContent({day}, '{language}')">
                <i class="fas fa-redo"></i> Retry
            </button>
        </div>
        '''
        return HttpResponse(error_content)


def _format_content_with_source_info(content_result, metadata):
    """Format content with source information."""
    if content_result.source == 'admin_managed':
        last_updated = metadata.last_updated.strftime('%Y-%m-%d %H:%M') if metadata.last_updated else 'Unknown'
        return f'''
        <div class="content-source-info">
            <small class="text-muted">
                <i class="fas fa-info-circle me-1"></i>
                <strong>Admin-managed content</strong> • 
                Last updated: {last_updated} • 
                Usage count: {metadata.usage_count}
                {f" • Title: {metadata.title}" if metadata.title else ""}
            </small>
        </div>
        '''
    elif content_result.source == 'static_fallback':
        return f'''
        <div class="content-source-info">
            <small class="text-muted">
                <i class="fas fa-file-alt me-1"></i>
                <strong>Static content</strong> • 
                Loaded from curriculum files • 
                No admin-managed content available for this day
            </small>
        </div>
        '''
    else:
        return f'''
        <div class="content-source-info">
            <small class="text-danger">
                <i class="fas fa-exclamation-triangle me-1"></i>
                <strong>Fallback content</strong> • 
                There was an issue loading the primary content
            </small>
        </div>
        '''


def _add_admin_management_links(content_result, day, language, user):
    """Add admin management links if user has permissions."""
    if user.role.name.upper() != "ADMIN":
        return ""
    
    if content_result.source == 'admin_managed' and content_result.curriculum_session:
        return f'''
        <div class="admin-actions">
            <small class="text-muted d-block mb-2">
                <i class="fas fa-tools me-1"></i>Admin Actions:
            </small>
            <a href="/admin/curriculum/session/{content_result.curriculum_session.id}/edit/" 
               class="btn btn-outline-primary btn-sm me-2" target="_blank">
                <i class="fas fa-edit me-1"></i>Edit Content
            </a>
            <a href="/admin/curriculum/session/{content_result.curriculum_session.id}/preview/" 
               class="btn btn-outline-info btn-sm" target="_blank">
                <i class="fas fa-eye me-1"></i>Preview
            </a>
        </div>
        '''
    else:
        return f'''
        <div class="admin-actions">
            <small class="text-muted d-block mb-2">
                <i class="fas fa-plus me-1"></i>Admin Actions:
            </small>
            <a href="/admin/curriculum/session/create/?day={day}&language={language}" 
               class="btn btn-outline-success btn-sm" target="_blank">
                <i class="fas fa-plus me-1"></i>Create Admin Content
            </a>
        </div>
        '''
        day_content = content[start_pos:end_pos]
        
        # Wrap in a proper HTML structure for display
        wrapped_content = f'''
        <div class="day-section" data-day="{day}" data-language="{language}">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Day {day} - {language.title()} Curriculum</h5>
                <span class="badge bg-info">{language.title()}</span>
            </div>
            <div class="table-responsive">
                <table class="table table-bordered curriculum-table">
                    <tbody>
                        {day_content}
                    </tbody>
                </table>
            </div>
        </div>
        <style>
        .curriculum-table {{
            font-size: 14px;
        }}
        .curriculum-table td {{
            padding: 8px;
            vertical-align: top;
        }}
        .curriculum-table .s0 {{
            background-color: #d9ead3;
            font-weight: bold;
            font-size: 18px;
            text-align: center;
        }}
        .curriculum-table .s1 {{
            background-color: #d9ead3;
            font-weight: bold;
            text-align: center;
        }}
        .curriculum-table .s4 {{
            background-color: #ffffff;
            font-weight: bold;
            text-align: center;
        }}
        .curriculum-table a {{
            color: #0066cc;
            text-decoration: underline;
        }}
        </style>
        '''
        
@login_required 
def facilitator_session_quick_nav(request, class_section_id):
    """Quick navigation API for facilitator sessions"""
    if request.user.role.name.upper() != "FACILITATOR":
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    class_section = get_object_or_404(ClassSection, id=class_section_id)
    
    # Get all session statuses
    sessions = PlannedSession.objects.filter(
        class_section=class_section,
        is_active=True
    ).prefetch_related('actual_sessions').order_by('day_number')
    
    session_data = []
    for session in sessions:
        latest_actual = session.actual_sessions.order_by("-date").first()
        status = latest_actual.status if latest_actual else "pending"
        
        session_data.append({
            'day': session.day_number,
            'status': status,
            'topic': session.topic,
            'date': latest_actual.date.isoformat() if latest_actual else None
        })
    
    return JsonResponse({
        'sessions': session_data,
        'class_info': {
            'school': class_section.school.name,
            'class': f"{class_section.class_level} - {class_section.section}"
        }
    })


@login_required
def facilitator_schools(request):
    """View for facilitator to see their assigned schools"""
    if request.user.role.name.upper() != "FACILITATOR":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    # Get schools assigned to this facilitator
    assigned_schools = FacilitatorSchool.objects.filter(
        facilitator=request.user,
        is_active=True
    ).select_related("school").order_by("school__name")

    return render(request, "facilitator/schools/list.html", {
        "assigned_schools": assigned_schools
    })


@login_required
def facilitator_school_detail(request, school_id):
    """View for facilitator to see classes in their assigned school"""
    if request.user.role.name.upper() != "FACILITATOR":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    # Verify facilitator has access to this school
    school = get_object_or_404(School, id=school_id)
    if not FacilitatorSchool.objects.filter(
        facilitator=request.user,
        school=school,
        is_active=True
    ).exists():
        messages.error(request, "You don't have access to this school.")
        return redirect("facilitator_schools")

    # Get classes for this school
    classes = ClassSection.objects.filter(
        school=school
    ).order_by("class_level", "section")

    return render(request, "facilitator/schools/detail.html", {
        "school": school,
        "classes": classes
    })


@login_required
def facilitator_students_list(request, class_section_id):
    """View for facilitator to see students in their assigned class"""
    if request.user.role.name.upper() != "FACILITATOR":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    class_section = get_object_or_404(ClassSection, id=class_section_id)
    
    # Verify facilitator has access to this class
    if not FacilitatorSchool.objects.filter(
        facilitator=request.user,
        school=class_section.school,
        is_active=True
    ).exists():
        messages.error(request, "You don't have access to this class.")
        return redirect("facilitator_schools")

    # Get students in this class with attendance statistics
    enrollments = Enrollment.objects.filter(
        class_section=class_section,
        is_active=True
    ).select_related(
        "student", 
        "school", 
        "class_section__school"
    ).prefetch_related(
        "attendances__actual_session"
    ).order_by("student__full_name")
    
    # Get total conducted sessions for this class (single query)
    total_sessions = ActualSession.objects.filter(
        planned_session__class_section=class_section,
        status="conducted"
    ).count()
    
    # Calculate attendance statistics for each student
    enrollment_stats = []
    for enrollment in enrollments:
        # Count attendance records for this student (using prefetched data when possible)
        present_count = Attendance.objects.filter(
            enrollment=enrollment,
            actual_session__planned_session__class_section=class_section,
            status="present"
        ).count()
        
        absent_count = Attendance.objects.filter(
            enrollment=enrollment,
            actual_session__planned_session__class_section=class_section,
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

    return render(request, "facilitator/students/list.html", {
        "class_section": class_section,
        "enrollments": enrollments,
        "enrollment_stats": enrollment_stats
    })


@login_required
def facilitator_student_detail(request, class_section_id, student_id):
    """View for facilitator to see student details and attendance"""
    if request.user.role.name.upper() != "FACILITATOR":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    class_section = get_object_or_404(ClassSection, id=class_section_id)
    student = get_object_or_404(Student, id=student_id)
    
    # Verify facilitator has access
    if not FacilitatorSchool.objects.filter(
        facilitator=request.user,
        school=class_section.school,
        is_active=True
    ).exists():
        messages.error(request, "You don't have access to this class.")
        return redirect("facilitator_schools")

    # Get enrollment
    enrollment = get_object_or_404(
        Enrollment,
        student=student,
        class_section=class_section,
        is_active=True
    )

    # Get attendance records
    attendance_records = Attendance.objects.filter(
        enrollment=enrollment
    ).select_related("actual_session__planned_session").order_by("-actual_session__date")[:20]

    # Calculate attendance stats
    total_sessions = ActualSession.objects.filter(
        planned_session__class_section=class_section,
        status="conducted"
    ).count()
    
    present_count = Attendance.objects.filter(
        enrollment=enrollment,
        status="present"
    ).count()
    
    absent_count = Attendance.objects.filter(
        enrollment=enrollment,
        status="absent"
    ).count()
    
    attendance_percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0

    return render(request, "facilitator/students/detail.html", {
        "class_section": class_section,
        "student": student,
        "enrollment": enrollment,
        "attendance_records": attendance_records,
        "stats": {
            "total_sessions": total_sessions,
            "present_count": present_count,
            "absent_count": absent_count,
            "attendance_percentage": round(attendance_percentage, 1)
        }
    })


@login_required
def facilitator_student_edit(request, class_section_id, student_id):
    """View for facilitator to edit student basic information"""
    if request.user.role.name.upper() != "FACILITATOR":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    class_section = get_object_or_404(ClassSection, id=class_section_id)
    student = get_object_or_404(Student, id=student_id)
    
    # Verify facilitator has access
    if not FacilitatorSchool.objects.filter(
        facilitator=request.user,
        school=class_section.school,
        is_active=True
    ).exists():
        messages.error(request, "You don't have access to this class.")
        return redirect("facilitator_schools")

    enrollment = get_object_or_404(
        Enrollment,
        student=student,
        class_section=class_section,
        is_active=True
    )

    if request.method == "POST":
        # Update student information
        student.full_name = request.POST.get("full_name", student.full_name)
        student.gender = request.POST.get("gender", student.gender)
        
        # Update enrollment information
        new_class_section_id = request.POST.get("class_section")
        if new_class_section_id and new_class_section_id != str(class_section.id):
            # Check if facilitator has access to new class
            new_class_section = get_object_or_404(ClassSection, id=new_class_section_id)
            if FacilitatorSchool.objects.filter(
                facilitator=request.user,
                school=new_class_section.school,
                is_active=True
            ).exists():
                enrollment.class_section = new_class_section
        
        try:
            student.save()
            enrollment.save()
            messages.success(request, f"Student {student.full_name} updated successfully!")
            return redirect("facilitator_class_students_list", class_section_id=enrollment.class_section.id)
        except Exception as e:
            messages.error(request, f"Error updating student: {str(e)}")

    # Get available classes for this facilitator
    available_classes = ClassSection.objects.filter(
        school__facilitators__facilitator=request.user,
        school__facilitators__is_active=True
    ).select_related("school").order_by("school__name", "class_level", "section")

    return render(request, "facilitator/students/edit.html", {
        "class_section": class_section,
        "student": student,
        "enrollment": enrollment,
        "available_classes": available_classes
    })


# ===== ADMIN CURRICULUM SESSION MANAGEMENT VIEWS =====

@login_required
@login_required
@monitor_performance
def admin_curriculum_sessions_list(request):
    """
    Admin view to display curriculum sessions with optimized pagination and filtering
    """
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    # Clear cache to ensure fresh data
    from django.core.cache import cache
    cache.clear()

    # Get filter parameters
    language_filter = request.GET.get('language', '')
    day_from = request.GET.get('day_from', '')
    day_to = request.GET.get('day_to', '')
    status_filter = request.GET.get('status', '')
    page = int(request.GET.get('page', 1))
    per_page = 50  # Limit to 50 sessions per page

    # Create cache key based on filters and page
    cache_key = f"curriculum_sessions_{language_filter}_{day_from}_{day_to}_{status_filter}_{page}_{request.user.id}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        context = cached_data
    else:
        # Optimized base queryset with select_related and only necessary fields
        sessions = CurriculumSession.objects.select_related('created_by').only(
            'id', 'title', 'day_number', 'language', 'status', 'updated_at', 'created_by__full_name'
        )

        # Apply filters
        if language_filter:
            sessions = sessions.filter(language=language_filter)
        
        if day_from:
            try:
                sessions = sessions.filter(day_number__gte=int(day_from))
            except ValueError:
                pass
        
        if day_to:
            try:
                sessions = sessions.filter(day_number__lte=int(day_to))
            except ValueError:
                pass
        
        if status_filter:
            sessions = sessions.filter(status=status_filter)

        # Order by language and day number
        sessions = sessions.order_by('language', 'day_number')

        # Get session counts by language with single query (only if no filters applied)
        if not any([language_filter, day_from, day_to, status_filter]):
            counts = CurriculumSession.objects.aggregate(
                hindi_count=Count('id', filter=Q(language='hindi')),
                english_count=Count('id', filter=Q(language='english'))
            )
        else:
            # Calculate counts based on filtered results
            counts = sessions.aggregate(
                hindi_count=Count('id', filter=Q(language='hindi')),
                english_count=Count('id', filter=Q(language='english'))
            )

        # Use pagination to limit results
        from django.core.paginator import Paginator
        paginator = Paginator(sessions, per_page)
        page_obj = paginator.get_page(page)

        # Group paginated sessions by language for display
        sessions_by_language = {'hindi': [], 'english': []}
        sessions_by_language_json = {'hindi': [], 'english': []}
        
        for session in page_obj:
            sessions_by_language[session.language].append(session)
            # Create JSON-serializable version for JavaScript
            sessions_by_language_json[session.language].append({
                'id': str(session.id),
                'title': session.title,
                'day_number': session.day_number,
                'language': session.language,
                'status': session.status,
                'updated_at': session.updated_at.isoformat() if session.updated_at else None,
            })

        context = {
            'sessions_by_language': sessions_by_language_json,  # For JavaScript
            'sessions_by_language_display': sessions_by_language,  # For template display
            'hindi_count': counts['hindi_count'],
            'english_count': counts['english_count'],
            'language_choices': CurriculumSession.LANGUAGE_CHOICES,
            'status_choices': CurriculumSession.STATUS_CHOICES,
            'page_obj': page_obj,
            'paginator': paginator,
            'filters': {
                'language': language_filter,
                'day_from': day_from,
                'day_to': day_to,
                'status': status_filter,
            }
        }
        
        # Cache for 2 minutes (shorter cache for better responsiveness)
        cache.set(cache_key, context, 120)

    # Add debugging information
    context['debug_template'] = "admin/sessions/curriculum_list.html"
    context['user_role'] = request.user.role.name.upper()
    context['debug_info'] = {
        'template_name': 'admin/sessions/curriculum_list.html',
        'base_template': 'admin/shared/base.html',
        'sidebar_template': 'admin/shared/sidebar.html',
        'user_role': request.user.role.name.upper(),
        'user_id': request.user.id,
    }
    
    # Convert sessions data to JSON for JavaScript
    import json
    context['sessions_by_language'] = json.dumps(context['sessions_by_language'])
    
    return render(request, "admin/sessions/curriculum_list.html", context)


@login_required
def admin_curriculum_session_create(request):
    """
    Enhanced admin view to create curriculum sessions with school/class filtering
    """
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    if request.method == "POST":
        title = request.POST.get("title")
        day_number = request.POST.get("day_number")
        language = request.POST.get("language")
        content = request.POST.get("content", "")
        learning_objectives = request.POST.get("learning_objectives", "")
        activities = request.POST.get("activities", "")
        resources = request.POST.get("resources", "")
        status = request.POST.get("status", "draft")
        
        # New bulk creation features
        create_multiple = request.POST.get("create_multiple") == "on"
        end_day_number = request.POST.get("end_day_number")
        target_schools = request.POST.getlist("target_schools")
        target_classes = request.POST.getlist("target_classes")

        try:
            day_number = int(day_number)
            
            if create_multiple and end_day_number:
                # Bulk creation for multiple days
                end_day = int(end_day_number)
                if end_day < day_number:
                    messages.error(request, "End day must be greater than start day.")
                    return render(request, "admin/sessions/curriculum_form.html", {
                        'language_choices': CurriculumSession.LANGUAGE_CHOICES,
                        'status_choices': CurriculumSession.STATUS_CHOICES,
                        'schools': School.objects.all().order_by('name'),
                        'form_data': request.POST
                    })
                
                created_sessions = []
                skipped_sessions = []
                
                for day in range(day_number, end_day + 1):
                    # Check for duplicate
                    if CurriculumSession.objects.filter(day_number=day, language=language).exists():
                        skipped_sessions.append(day)
                        continue
                    
                    # Create session for this day
                    session = CurriculumSession.objects.create(
                        title=f"{title} - Day {day}",
                        day_number=day,
                        language=language,
                        content=content.replace("{DAY}", str(day)) if content else "",
                        learning_objectives=learning_objectives.replace("{DAY}", str(day)) if learning_objectives else "",
                        activities={"template": activities} if activities else {},
                        resources={"template": resources} if resources else {},
                        status=status,
                        created_by=request.user
                    )
                    created_sessions.append(session)
                
                # Success message
                success_msg = f"Created {len(created_sessions)} curriculum sessions"
                if skipped_sessions:
                    success_msg += f" (Skipped {len(skipped_sessions)} existing sessions: Days {', '.join(map(str, skipped_sessions))})"
                
                # Auto-create planned sessions for all classes that don't have them
                auto_create_planned_sessions_for_all_classes()
                
                messages.success(request, success_msg)
                return redirect("admin_curriculum_sessions_list")
            
            else:
                # Single session creation
                if CurriculumSession.objects.filter(day_number=day_number, language=language).exists():
                    messages.error(request, f"A session for Day {day_number} in {language.title()} already exists.")
                    return render(request, "admin/sessions/curriculum_form.html", {
                        'language_choices': CurriculumSession.LANGUAGE_CHOICES,
                        'status_choices': CurriculumSession.STATUS_CHOICES,
                        'schools': School.objects.all().order_by('name'),
                        'form_data': request.POST
                    })

                # Create the session
                session = CurriculumSession.objects.create(
                    title=title,
                    day_number=day_number,
                    language=language,
                    content=content,
                    learning_objectives=learning_objectives,
                    activities={"content": activities} if activities else {},
                    resources={"content": resources} if resources else {},
                    status=status,
                    created_by=request.user
                )

                # Auto-create planned sessions for all classes that don't have them
                auto_create_planned_sessions_for_all_classes()

                messages.success(request, f"Curriculum session '{title}' created successfully!")
                return redirect("admin_curriculum_sessions_list")

        except ValueError:
            messages.error(request, "Invalid day number. Please enter a number between 1 and 150.")
        except Exception as e:
            messages.error(request, f"Error creating session: {str(e)}")

    # GET request - show form
    context = {
        'language_choices': CurriculumSession.LANGUAGE_CHOICES,
        'status_choices': CurriculumSession.STATUS_CHOICES,
        'schools': School.objects.all().order_by('name'),
        'is_create': True,
        # Pre-fill from URL parameters
        'prefill_day': request.GET.get('day'),
        'prefill_language': request.GET.get('language'),
    }

    return render(request, "admin/sessions/curriculum_form.html", context)


@login_required
def admin_curriculum_session_edit(request, session_id):
    """
    Admin view to edit an existing curriculum session
    """
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    session = get_object_or_404(CurriculumSession, id=session_id)

    if request.method == "POST":
        # Create version history before updating
        version_number = session.version_history.count() + 1
        SessionVersionHistory.objects.create(
            session=session,
            version_number=version_number,
            title=session.title,
            content=session.content,
            learning_objectives=session.learning_objectives,
            activities=session.activities,
            resources=session.resources,
            modified_by=request.user,
            change_summary=request.POST.get("change_summary", "")
        )

        # Update session
        session.title = request.POST.get("title", session.title)
        session.day_number = int(request.POST.get("day_number", session.day_number))
        session.language = request.POST.get("language", session.language)
        session.content = request.POST.get("content", session.content)
        session.learning_objectives = request.POST.get("learning_objectives", session.learning_objectives)
        session.status = request.POST.get("status", session.status)

        try:
            # Check for duplicate day number within same language (excluding current session)
            if CurriculumSession.objects.filter(
                day_number=session.day_number, 
                language=session.language
            ).exclude(id=session.id).exists():
                messages.error(request, f"A session for Day {session.day_number} in {session.language.title()} already exists.")
                return render(request, "admin/sessions/curriculum_form.html", {
                    'session': session,
                    'language_choices': CurriculumSession.LANGUAGE_CHOICES,
                    'status_choices': CurriculumSession.STATUS_CHOICES,
                    'is_edit': True
                })

            session.save()
            messages.success(request, f"Curriculum session '{session.title}' updated successfully!")
            return redirect("admin_curriculum_sessions_list")

        except Exception as e:
            messages.error(request, f"Error updating session: {str(e)}")

    context = {
        'session': session,
        'language_choices': CurriculumSession.LANGUAGE_CHOICES,
        'status_choices': CurriculumSession.STATUS_CHOICES,
        'is_edit': True
    }

    return render(request, "admin/sessions/curriculum_form.html", context)


@login_required
def admin_curriculum_session_delete(request, session_id):
    """
    Admin view to delete a curriculum session
    """
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    session = get_object_or_404(CurriculumSession, id=session_id)

    if request.method == "POST":
        session_title = session.title
        session.delete()
        messages.success(request, f"Curriculum session '{session_title}' deleted successfully!")
        return redirect("admin_curriculum_sessions_list")

    return render(request, "admin/sessions/curriculum_delete.html", {
        'session': session
    })


@login_required
def admin_curriculum_session_preview(request, session_id):
    """
    Admin view to preview how a session will appear to facilitators
    """
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    session = get_object_or_404(CurriculumSession, id=session_id)

    # Get navigation context
    prev_session = CurriculumSession.objects.filter(
        language=session.language,
        day_number__lt=session.day_number
    ).order_by('-day_number').first()

    next_session = CurriculumSession.objects.filter(
        language=session.language,
        day_number__gt=session.day_number
    ).order_by('day_number').first()

    context = {
        'session': session,
        'prev_session': prev_session,
        'next_session': next_session,
        'is_preview': True
    }

    return render(request, "admin/sessions/curriculum_preview.html", context)

# ===== LAZY LOADING API ENDPOINTS =====

@login_required
@monitor_performance
def api_lazy_load_sessions(request):
    """
    API endpoint for lazy loading curriculum sessions
    """
    if request.user.role.name.upper() != "ADMIN":
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    # Get pagination parameters
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    language = request.GET.get('language', '')
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Build query
    queryset = CurriculumSession.objects.select_related('created_by')
    
    if language:
        queryset = queryset.filter(language=language)
    
    # Get total count
    total_count = queryset.count()
    
    # Get paginated results
    sessions = queryset.order_by('day_number')[offset:offset + per_page]
    
    # Serialize data
    sessions_data = []
    for session in sessions:
        sessions_data.append({
            'id': str(session.id),
            'title': session.title,
            'day_number': session.day_number,
            'language': session.get_language_display(),
            'status': session.get_status_display(),
            'created_by': session.created_by.full_name if session.created_by else 'System',
            'updated_at': session.updated_at.strftime('%b %d, %Y %H:%M'),
            'preview_url': f'/admin/curriculum-sessions/{session.id}/preview/',
            'edit_url': f'/admin/curriculum-sessions/{session.id}/edit/',
            'delete_url': f'/admin/curriculum-sessions/{session.id}/delete/',
        })
    
    response_data = {
        'sessions': sessions_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': (total_count + per_page - 1) // per_page,
            'has_next': offset + per_page < total_count,
            'has_previous': page > 1,
        }
    }
    
    response = JsonResponse(response_data)
    response['Cache-Control'] = 'max-age=300'  # 5 minutes cache
    return response


@login_required
@monitor_performance
def api_lazy_load_schools(request):
    """
    API endpoint for lazy loading schools with statistics
    """
    if request.user.role.name.upper() != "ADMIN":
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 10))
    search = request.GET.get('search', '')
    
    offset = (page - 1) * per_page
    
    # Build optimized query
    queryset = School.objects.select_related().prefetch_related(
        'class_sections',
        'facilitators__facilitator'
    ).annotate(
        total_classes=Count('class_sections', distinct=True),
        total_students=Count('class_sections__enrollments', 
                           filter=Q(class_sections__enrollments__is_active=True),
                           distinct=True),
        active_facilitators=Count('facilitators', 
                                filter=Q(facilitators__is_active=True),
                                distinct=True)
    )
    
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | 
            Q(district__icontains=search) |
            Q(state__icontains=search)
        )
    
    total_count = queryset.count()
    schools = queryset.order_by('-created_at')[offset:offset + per_page]
    
    schools_data = []
    for school in schools:
        schools_data.append({
            'id': str(school.id),
            'name': school.name,
            'district': school.district,
            'state': school.state,
            'total_classes': school.total_classes,
            'total_students': school.total_students,
            'active_facilitators': school.active_facilitators,
            'created_at': school.created_at.strftime('%b %d, %Y'),
            'detail_url': f'/admin/schools/{school.id}/',
            'edit_url': f'/admin/schools/{school.id}/edit/',
        })
    
    response_data = {
        'schools': schools_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': (total_count + per_page - 1) // per_page,
            'has_next': offset + per_page < total_count,
            'has_previous': page > 1,
        }
    }
    
    response = JsonResponse(response_data)
    response['Cache-Control'] = 'max-age=600'  # 10 minutes cache
    return response


@login_required
@monitor_performance  
def api_dashboard_stats(request):
    """
    API endpoint for dashboard statistics with caching
    """
    if request.user.role.name.upper() != "ADMIN":
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    cache_key = f"dashboard_stats_{request.user.id}"
    stats = cache.get(cache_key)
    
    if stats is None:
        today = timezone.now().date()
        
        # Use aggregation for better performance
        school_stats = School.objects.aggregate(
            active_schools=Count('id', filter=Q(status=1)),
            total_schools=Count('id')
        )
        
        user_stats = User.objects.aggregate(
            active_facilitators=Count('id', filter=Q(
                role__name__iexact="FACILITATOR",
                is_active=True
            )),
            total_users=Count('id')
        )
        
        enrollment_stats = Enrollment.objects.aggregate(
            enrolled_students=Count('id', filter=Q(is_active=True))
        )
        
        session_stats = ActualSession.objects.filter(date=today).aggregate(
            sessions_today=Count('id', filter=Q(status="conducted")),
            holidays_today=Count('id', filter=Q(status="holiday")),
            cancelled_today=Count('id', filter=Q(status="cancelled"))
        )
        
        curriculum_stats = CurriculumSession.objects.aggregate(
            hindi_sessions=Count('id', filter=Q(language='hindi')),
            english_sessions=Count('id', filter=Q(language='english')),
            total_curriculum=Count('id')
        )
        
        stats = {
            **school_stats,
            **user_stats,
            **enrollment_stats,
            **session_stats,
            **curriculum_stats,
            'last_updated': timezone.now().isoformat()
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, stats, 300)
    
    response = JsonResponse(stats)
    response['Cache-Control'] = 'max-age=300'
    return response


@login_required
@monitor_performance
def api_dashboard_recent_sessions(request):
    """
    API endpoint for recent class sessions with optimized loading
    """
    if request.user.role.name.upper() != "ADMIN":
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    try:
        limit = min(int(request.GET.get('limit', 10)), 50)  # Max 50 items
        
        cache_key = f"recent_sessions_{limit}_{request.user.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            response = JsonResponse(cached_data)
            response['Cache-Control'] = 'max-age=300'
            return response
        
        # Get recent class sessions with optimized query
        recent_sessions = ActualSession.objects.select_related(
            'planned_session',
            'facilitator', 
            'planned_session__class_section__school'
        ).order_by('-created_at')[:limit]
        
        sessions_data = []
        for session in recent_sessions:
            sessions_data.append({
                'id': str(session.id),
                'topic': session.planned_session.topic if session.planned_session else 'N/A',
                'class_section': str(session.planned_session.class_section) if session.planned_session else 'N/A',
                'school': session.planned_session.class_section.school.name if session.planned_session and session.planned_session.class_section else 'N/A',
                'facilitator': session.facilitator.full_name if session.facilitator else 'N/A',
                'status': session.status,
                'date': session.date.strftime('%Y-%m-%d') if session.date else None,
                'created_at': session.created_at.strftime('%b %d, %Y %H:%M'),
                'time_ago': session.created_at.strftime('%b %d')
            })
        
        response_data = {
            'sessions': sessions_data,
            'count': len(sessions_data),
            'last_updated': timezone.now().isoformat()
        }
        
        # Cache for 2 minutes
        cache.set(cache_key, response_data, 120)
        
        response = JsonResponse(response_data)
        response['Cache-Control'] = 'max-age=120'
        return response
        
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to load recent sessions',
            'message': str(e)
        }, status=500)


@login_required
@monitor_performance
def api_dashboard_curriculum_updates(request):
    """
    API endpoint for recent curriculum updates with optimized loading
    """
    if request.user.role.name.upper() != "ADMIN":
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    try:
        limit = min(int(request.GET.get('limit', 10)), 50)  # Max 50 items
        
        cache_key = f"curriculum_updates_{limit}_{request.user.id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            response = JsonResponse(cached_data)
            response['Cache-Control'] = 'max-age=300'
            return response
        
        # Get recent curriculum updates with optimized query
        recent_updates = CurriculumSession.objects.select_related(
            'created_by'
        ).order_by('-updated_at')[:limit]
        
        updates_data = []
        for session in recent_updates:
            updates_data.append({
                'id': str(session.id),
                'title': session.title,
                'day_number': session.day_number,
                'language': session.get_language_display(),
                'status': session.get_status_display(),
                'created_by': session.created_by.full_name if session.created_by else 'System',
                'updated_at': session.updated_at.strftime('%b %d, %Y %H:%M'),
                'time_ago': session.updated_at.strftime('%b %d'),
                'preview_url': f'/admin/curriculum-sessions/{session.id}/preview/',
                'edit_url': f'/admin/curriculum-sessions/{session.id}/edit/'
            })
        
        response_data = {
            'updates': updates_data,
            'count': len(updates_data),
            'last_updated': timezone.now().isoformat()
        }
        
        # Cache for 2 minutes
        cache.set(cache_key, response_data, 120)
        
        response = JsonResponse(response_data)
        response['Cache-Control'] = 'max-age=120'
        return response
        
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to load curriculum updates',
            'message': str(e)
        }, status=500)


@login_required
def admin_sessions_overview(request):
    """
    Admin overview showing both class-based sessions and curriculum sessions
    """
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    # Get class-based session statistics
    total_schools = School.objects.filter(status=1).count()
    total_classes = ClassSection.objects.filter(is_active=True).count()
    total_planned_sessions = PlannedSession.objects.filter(is_active=True).count()
    total_actual_sessions = ActualSession.objects.count()

    # Get curriculum session statistics
    total_curriculum_sessions = CurriculumSession.objects.count()
    hindi_sessions = CurriculumSession.objects.filter(language='hindi').count()
    english_sessions = CurriculumSession.objects.filter(language='english').count()
    published_sessions = CurriculumSession.objects.filter(status='published').count()

    # Recent activity from both systems
    recent_class_sessions = ActualSession.objects.select_related(
        'planned_session', 'facilitator', 'planned_session__class_section__school'
    ).order_by('-created_at')[:5]

    recent_curriculum_updates = CurriculumSession.objects.select_related(
        'created_by'
    ).order_by('-updated_at')[:5]

    context = {
        # Class-based session stats
        'total_schools': total_schools,
        'total_classes': total_classes,
        'total_planned_sessions': total_planned_sessions,
        'total_actual_sessions': total_actual_sessions,
        
        # Curriculum session stats
        'total_curriculum_sessions': total_curriculum_sessions,
        'hindi_sessions': hindi_sessions,
        'english_sessions': english_sessions,
        'published_sessions': published_sessions,
        
        # Recent activity
        'recent_class_sessions': recent_class_sessions,
        'recent_curriculum_updates': recent_curriculum_updates,
    }

    return render(request, "admin/sessions/overview.html", context)
@login_required
@monitor_performance
def ajax_school_classes_admin(request):
    """AJAX endpoint to get classes for specific school(s) (admin version) - Enhanced"""
    if request.user.role.name.upper() != "ADMIN":
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    # Support both single school_id and multiple schools parameters
    school_id = request.GET.get("school_id")
    schools_param = request.GET.get("schools")
    
    if not school_id and not schools_param:
        return JsonResponse({"error": "School ID or schools parameter required"}, status=400)
    
    try:
        if schools_param:
            # Multiple schools for curriculum targeting
            school_ids = schools_param.split(',')
            cache_key = f"multiple_school_classes_{'_'.join(sorted(school_ids))}"
        else:
            # Single school for backward compatibility
            school_ids = [school_id]
            cache_key = f"school_classes_{school_id}"
        
        classes_data = cache.get(cache_key)
        
        if classes_data is None:
            classes = ClassSection.objects.filter(
                school_id__in=school_ids,
                is_active=True
            ).select_related('school').order_by('school__name', 'class_level', 'section')
            
            classes_data = []
            for cls in classes:
                classes_data.append({
                    'id': str(cls.id),
                    'class_level': cls.class_level,
                    'section': cls.section or '',
                    'display_name': cls.display_name or f"{cls.class_level}{cls.section or ''}",
                    'school_name': cls.school.name,
                    'school_id': str(cls.school.id)
                })
            
            # Cache for 10 minutes
            cache.set(cache_key, classes_data, 600)
        
        response = JsonResponse({
            "success": True,
            "classes": classes_data,
            "count": len(classes_data)
        })
        response['Cache-Control'] = 'max-age=600'  # 10 minutes browser cache
        return response
        
    except Exception as e:
        logger.error(f"Error fetching classes for schools {school_ids}: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@monitor_performance
def api_curriculum_sessions_filter(request):
    """
    AJAX API endpoint for fast curriculum session filtering without page reload
    """
    if request.user.role.name.upper() != "ADMIN":
        return JsonResponse({"error": "Permission denied"}, status=403)
    
    try:
        # Get filter parameters
        language_filter = request.GET.get('language', '')
        day_from = request.GET.get('day_from', '')
        day_to = request.GET.get('day_to', '')
        status_filter = request.GET.get('status', '')
        page = int(request.GET.get('page', 1))
        per_page = 25  # Smaller page size for AJAX
        
        # Create cache key
        cache_key = f"curriculum_filter_{language_filter}_{day_from}_{day_to}_{status_filter}_{page}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            response = JsonResponse(cached_data)
            response['Cache-Control'] = 'max-age=60'
            return response
        
        # Optimized query with only necessary fields
        sessions = CurriculumSession.objects.select_related('created_by').only(
            'id', 'title', 'day_number', 'language', 'status', 'updated_at', 'created_by__full_name'
        )
        
        # Apply filters
        if language_filter:
            sessions = sessions.filter(language=language_filter)
        
        if day_from:
            try:
                sessions = sessions.filter(day_number__gte=int(day_from))
            except ValueError:
                pass
        
        if day_to:
            try:
                sessions = sessions.filter(day_number__lte=int(day_to))
            except ValueError:
                pass
        
        if status_filter:
            sessions = sessions.filter(status=status_filter)
        
        # Order and paginate
        sessions = sessions.order_by('language', 'day_number')
        
        # Get total count for pagination
        total_count = sessions.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        sessions_page = sessions[offset:offset + per_page]
        
        # Serialize sessions
        sessions_data = []
        for session in sessions_page:
            sessions_data.append({
                'id': str(session.id),
                'title': session.title,
                'day_number': session.day_number,
                'language': session.language,
                'language_display': session.get_language_display(),
                'status': session.status,
                'status_display': session.get_status_display(),
                'created_by': session.created_by.full_name if session.created_by else 'System',
                'updated_at': session.updated_at.strftime('%b %d, %Y %H:%M'),
                'preview_url': f'/admin/curriculum-sessions/{session.id}/preview/',
                'edit_url': f'/admin/curriculum-sessions/{session.id}/edit/',
                'delete_url': f'/admin/curriculum-sessions/{session.id}/delete/',
            })
        
        # Get counts by language
        if not any([language_filter, day_from, day_to, status_filter]):
            counts = CurriculumSession.objects.aggregate(
                hindi_count=Count('id', filter=Q(language='hindi')),
                english_count=Count('id', filter=Q(language='english'))
            )
        else:
            # Calculate counts based on filtered results (without pagination)
            counts = sessions.aggregate(
                hindi_count=Count('id', filter=Q(language='hindi')),
                english_count=Count('id', filter=Q(language='english'))
            )
        
        response_data = {
            'sessions': sessions_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': (total_count + per_page - 1) // per_page,
                'has_next': offset + per_page < total_count,
                'has_previous': page > 1,
            },
            'counts': counts,
            'filters': {
                'language': language_filter,
                'day_from': day_from,
                'day_to': day_to,
                'status': status_filter,
            }
        }
        
        # Cache for 1 minute
        cache.set(cache_key, response_data, 60)
        
        response = JsonResponse(response_data)
        response['Cache-Control'] = 'max-age=60'
        return response
        
    except Exception as e:
        logger.error(f"Error in curriculum sessions filter API: {str(e)}")
        return JsonResponse({
            'error': 'Failed to filter sessions',
            'message': str(e)
        }, status=500)

# =========================
# SESSION WORKFLOW VIEWS
# =========================

@login_required
def upload_lesson_plan(request):
    """Upload lesson plan for a planned session"""
    if request.user.role.name.upper() != "FACILITATOR":
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
    
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)
    
    try:
        planned_session_id = request.POST.get('planned_session_id')
        planned_session = get_object_or_404(PlannedSession, id=planned_session_id)
        
        # Verify facilitator has access to this class
        if not FacilitatorSchool.objects.filter(
            facilitator=request.user,
            school=planned_session.class_section.school,
            is_active=True
        ).exists():
            return JsonResponse({"success": False, "error": "Access denied"}, status=403)
        
        lesson_plan_file = request.FILES.get('lesson_plan_file')
        if not lesson_plan_file:
            return JsonResponse({"success": False, "error": "No file uploaded"}, status=400)
        
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx']
        file_extension = os.path.splitext(lesson_plan_file.name)[1].lower()
        if file_extension not in allowed_extensions:
            return JsonResponse({"success": False, "error": "Invalid file type. Only PDF, DOC, and DOCX files are allowed."}, status=400)
        
        # Validate file size (max 10MB)
        if lesson_plan_file.size > 10 * 1024 * 1024:
            return JsonResponse({"success": False, "error": "File too large. Maximum size is 10MB."}, status=400)
        
        upload_notes = request.POST.get('upload_notes', '')
        
        # Create or update lesson plan upload
        from .models import LessonPlanUpload
        lesson_plan_upload, created = LessonPlanUpload.objects.update_or_create(
            planned_session=planned_session,
            facilitator=request.user,
            defaults={
                'lesson_plan_file': lesson_plan_file,
                'file_name': lesson_plan_file.name,
                'file_size': lesson_plan_file.size,
                'upload_notes': upload_notes,
                'is_approved': False
            }
        )
        
        return JsonResponse({
            "success": True,
            "message": "Lesson plan uploaded successfully",
            "upload_id": str(lesson_plan_upload.id),
            "file_name": lesson_plan_upload.file_name,
            "file_size": lesson_plan_upload.file_size
        })
        
    except Exception as e:
        logger.error(f"Error uploading lesson plan: {e}")
        return JsonResponse({"success": False, "error": "Upload failed. Please try again."}, status=500)


@login_required
def save_preparation_checklist(request):
    """Save preparation checklist progress"""
    if request.user.role.name.upper() != "FACILITATOR":
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
    
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)
    
    try:
        planned_session_id = request.POST.get('planned_session_id')
        planned_session = get_object_or_404(PlannedSession, id=planned_session_id)
        
        # Verify facilitator has access to this class
        if not FacilitatorSchool.objects.filter(
            facilitator=request.user,
            school=planned_session.class_section.school,
            is_active=True
        ).exists():
            return JsonResponse({"success": False, "error": "Access denied"}, status=403)
        
        from .models import SessionPreparationChecklist
        
        # Get or create preparation checklist
        checklist, created = SessionPreparationChecklist.objects.get_or_create(
            planned_session=planned_session,
            facilitator=request.user,
            defaults={
                'preparation_start_time': timezone.now()
            }
        )
        
        # Update checkpoint values
        checklist.lesson_plan_reviewed = request.POST.get('lesson_plan_reviewed') == 'on'
        checklist.materials_prepared = request.POST.get('materials_prepared') == 'on'
        checklist.technology_tested = request.POST.get('technology_tested') == 'on'
        checklist.classroom_setup_ready = request.POST.get('classroom_setup_ready') == 'on'
        checklist.student_list_reviewed = request.POST.get('student_list_reviewed') == 'on'
        checklist.previous_session_feedback_reviewed = request.POST.get('previous_session_feedback_reviewed') == 'on'
        checklist.preparation_notes = request.POST.get('preparation_notes', '')
        
        # Update timestamps for completed checkpoints
        current_time = timezone.now().isoformat()
        checkpoints_completed_at = checklist.checkpoints_completed_at or {}
        
        checkpoint_fields = [
            'lesson_plan_reviewed', 'materials_prepared', 'technology_tested',
            'classroom_setup_ready', 'student_list_reviewed', 'previous_session_feedback_reviewed'
        ]
        
        for field in checkpoint_fields:
            if getattr(checklist, field) and field not in checkpoints_completed_at:
                checkpoints_completed_at[field] = current_time
            elif not getattr(checklist, field) and field in checkpoints_completed_at:
                del checkpoints_completed_at[field]
        
        checklist.checkpoints_completed_at = checkpoints_completed_at
        
        # Check if all checkpoints are completed
        all_completed = all(getattr(checklist, field) for field in checkpoint_fields)
        if all_completed and not checklist.preparation_complete_time:
            checklist.preparation_complete_time = timezone.now()
            
            # Calculate total preparation time
            if checklist.preparation_start_time:
                time_diff = checklist.preparation_complete_time - checklist.preparation_start_time
                checklist.total_preparation_minutes = int(time_diff.total_seconds() / 60)
        
        checklist.save()
        
        return JsonResponse({
            "success": True,
            "message": "Preparation checklist saved",
            "completion_percentage": checklist.completion_percentage,
            "all_completed": all_completed
        })
        
    except Exception as e:
        logger.error(f"Error saving preparation checklist: {e}")
        return JsonResponse({"success": False, "error": "Failed to save checklist"}, status=500)


@login_required
def save_session_reward(request):
    """Save session reward information"""
    if request.user.role.name.upper() != "FACILITATOR":
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
    
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)
    
    try:
        planned_session_id = request.POST.get('planned_session_id')
        planned_session = get_object_or_404(PlannedSession, id=planned_session_id)
        
        # Verify facilitator has access to this class
        if not FacilitatorSchool.objects.filter(
            facilitator=request.user,
            school=planned_session.class_section.school,
            is_active=True
        ).exists():
            return JsonResponse({"success": False, "error": "Access denied"}, status=403)
        
        # Get or create actual session (for rewards, we need a session that's being conducted)
        actual_session, created = ActualSession.objects.get_or_create(
            planned_session=planned_session,
            date=timezone.now().date(),
            defaults={
                'facilitator': request.user,
                'status': 'conducted',  # Assume session is being conducted when rewards are given
                'remarks': 'Session in progress - rewards recorded'
            }
        )
        
        reward_type = request.POST.get('reward_type', 'text')
        reward_description = request.POST.get('reward_description', '')
        student_names = request.POST.get('student_names', '')
        reward_photo = request.FILES.get('reward_photo')
        
        if not reward_description:
            return JsonResponse({"success": False, "error": "Reward description is required"}, status=400)
        
        from .models import SessionReward
        
        # Create reward record
        reward = SessionReward.objects.create(
            actual_session=actual_session,
            facilitator=request.user,
            reward_type=reward_type,
            reward_description=reward_description,
            student_names=student_names,
            reward_photo=reward_photo,
            is_visible_to_admin=True
        )
        
        return JsonResponse({
            "success": True,
            "message": "Reward information saved successfully",
            "reward_id": str(reward.id)
        })
        
    except Exception as e:
        logger.error(f"Error saving session reward: {e}")
        return JsonResponse({"success": False, "error": "Failed to save reward information"}, status=500)


@login_required
def save_session_tracking(request):
    """Save real-time session tracking data"""
    if request.user.role.name.upper() != "FACILITATOR":
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
    
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)
    
    try:
        planned_session_id = request.POST.get('planned_session_id')
        planned_session = get_object_or_404(PlannedSession, id=planned_session_id)
        
        # Verify facilitator has access to this class
        if not FacilitatorSchool.objects.filter(
            facilitator=request.user,
            school=planned_session.class_section.school,
            is_active=True
        ).exists():
            return JsonResponse({"success": False, "error": "Access denied"}, status=403)
        
        from .models import SessionFeedback
        
        # Get or create session feedback for tracking
        feedback, created = SessionFeedback.objects.get_or_create(
            actual_session__planned_session=planned_session,
            facilitator=request.user,
            defaults={
                'student_engagement_level': 3,
                'student_understanding_level': 3,
                'session_completion_percentage': 0,
                'time_management_rating': 3,
                'content_difficulty_rating': 3,
                'facilitator_satisfaction': 3,
                'what_went_well': '',
                'areas_for_improvement': '',
                'is_complete': False
            }
        )
        
        # Update tracking fields
        if request.POST.get('student_engagement_level'):
            feedback.student_engagement_level = int(request.POST.get('student_engagement_level'))
        
        if request.POST.get('student_understanding_level'):
            feedback.student_understanding_level = int(request.POST.get('student_understanding_level'))
        
        feedback.student_questions = request.POST.get('student_questions', feedback.student_questions)
        feedback.challenging_topics = request.POST.get('challenging_topics', feedback.challenging_topics)
        feedback.student_participation_notes = request.POST.get('student_participation_notes', feedback.student_participation_notes)
        
        feedback.save()
        
        return JsonResponse({
            "success": True,
            "message": "Session tracking data saved"
        })
        
    except Exception as e:
        logger.error(f"Error saving session tracking: {e}")
        return JsonResponse({"success": False, "error": "Failed to save tracking data"}, status=500)


@login_required
def save_session_feedback(request):
    """Save comprehensive session feedback"""
    if request.user.role.name.upper() != "FACILITATOR":
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
    
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)
    
    try:
        planned_session_id = request.POST.get('planned_session_id')
        planned_session = get_object_or_404(PlannedSession, id=planned_session_id)
        
        # Verify facilitator has access to this class
        if not FacilitatorSchool.objects.filter(
            facilitator=request.user,
            school=planned_session.class_section.school,
            is_active=True
        ).exists():
            return JsonResponse({"success": False, "error": "Access denied"}, status=403)
        
        # Get or create actual session
        actual_session, created = ActualSession.objects.get_or_create(
            planned_session=planned_session,
            date=timezone.now().date(),
            defaults={
                'facilitator': request.user,
                'status': 'conducted',
                'remarks': 'Session completed with feedback'
            }
        )
        
        from .models import SessionFeedback
        
        # Validate required fields
        required_fields = [
            'session_completion_percentage', 'time_management_rating', 'content_difficulty_rating',
            'facilitator_satisfaction', 'what_went_well', 'areas_for_improvement'
        ]
        
        for field in required_fields:
            if not request.POST.get(field):
                return JsonResponse({"success": False, "error": f"{field.replace('_', ' ').title()} is required"}, status=400)
        
        # Create or update feedback
        feedback, created = SessionFeedback.objects.update_or_create(
            actual_session=actual_session,
            facilitator=request.user,
            defaults={
                'student_engagement_level': int(request.POST.get('student_engagement_level', 3)),
                'student_understanding_level': int(request.POST.get('student_understanding_level', 3)),
                'student_participation_notes': request.POST.get('student_participation_notes', ''),
                'learning_objectives_met': request.POST.get('learning_objectives_met') == 'on',
                'challenging_topics': request.POST.get('challenging_topics', ''),
                'student_questions': request.POST.get('student_questions', ''),
                'session_completion_percentage': int(request.POST.get('session_completion_percentage')),
                'time_management_rating': int(request.POST.get('time_management_rating')),
                'content_difficulty_rating': int(request.POST.get('content_difficulty_rating')),
                'facilitator_satisfaction': int(request.POST.get('facilitator_satisfaction')),
                'what_went_well': request.POST.get('what_went_well'),
                'areas_for_improvement': request.POST.get('areas_for_improvement'),
                'next_session_preparation': request.POST.get('next_session_preparation', ''),
                'additional_notes': request.POST.get('additional_notes', ''),
                'is_complete': True
            }
        )
        
        return JsonResponse({
            "success": True,
            "message": "Session feedback saved successfully. You can now conduct the session.",
            "feedback_id": str(feedback.id)
        })
        
    except Exception as e:
        logger.error(f"Error saving session feedback: {e}")
        return JsonResponse({"success": False, "error": "Failed to save feedback"}, status=500)


@login_required
def save_student_feedback(request):
    """Save anonymous student feedback for a session"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)
    
    try:
        actual_session_id = request.POST.get('actual_session_id')
        actual_session = get_object_or_404(ActualSession, id=actual_session_id)
        
        # Validate required fields
        required_fields = [
            'session_rating', 'topic_understanding', 'teacher_clarity',
            'session_highlights', 'improvement_suggestions', 'anonymous_student_id'
        ]
        
        for field in required_fields:
            if not request.POST.get(field):
                return JsonResponse({"success": False, "error": f"{field.replace('_', ' ').title()} is required"}, status=400)
        
        from .models import StudentFeedback
        
        # Create student feedback
        feedback = StudentFeedback.objects.create(
            actual_session=actual_session,
            anonymous_student_id=request.POST.get('anonymous_student_id'),
            session_rating=int(request.POST.get('session_rating')),
            topic_understanding=request.POST.get('topic_understanding'),
            teacher_clarity=request.POST.get('teacher_clarity'),
            session_highlights=request.POST.get('session_highlights'),
            improvement_suggestions=request.POST.get('improvement_suggestions'),
            additional_suggestions=request.POST.get('additional_suggestions', ''),
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Update analytics
        from .models import FeedbackAnalytics
        analytics, created = FeedbackAnalytics.objects.get_or_create(
            actual_session=actual_session
        )
        analytics.calculate_analytics()
        
        return JsonResponse({
            "success": True,
            "message": "Student feedback submitted successfully!",
            "feedback_id": str(feedback.id)
        })
        
    except Exception as e:
        logger.error(f"Error saving student feedback: {e}")
        return JsonResponse({"success": False, "error": "Failed to save student feedback"}, status=500)


@login_required
def save_teacher_feedback(request):
    """Save teacher reflection feedback for a session"""
    if request.user.role.name.upper() != "FACILITATOR":
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
    
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)
    
    try:
        actual_session_id = request.POST.get('actual_session_id')
        actual_session = get_object_or_404(ActualSession, id=actual_session_id)
        
        # Verify facilitator has access to this session
        if actual_session.facilitator != request.user:
            return JsonResponse({"success": False, "error": "Access denied"}, status=403)
        
        # Validate required fields
        required_fields = [
            'class_engagement', 'session_completion', 'student_struggles',
            'successful_elements', 'improvement_areas'
        ]
        
        for field in required_fields:
            if not request.POST.get(field):
                return JsonResponse({"success": False, "error": f"{field.replace('_', ' ').title()} is required"}, status=400)
        
        from .models import TeacherFeedback
        
        # Create or update teacher feedback
        feedback, created = TeacherFeedback.objects.update_or_create(
            actual_session=actual_session,
            facilitator=request.user,
            defaults={
                'class_engagement': request.POST.get('class_engagement'),
                'session_completion': request.POST.get('session_completion'),
                'student_struggles': request.POST.get('student_struggles'),
                'successful_elements': request.POST.get('successful_elements'),
                'improvement_areas': request.POST.get('improvement_areas'),
                'resource_needs': request.POST.get('resource_needs', '')
            }
        )
        
        # Update analytics
        from .models import FeedbackAnalytics
        analytics, created = FeedbackAnalytics.objects.get_or_create(
            actual_session=actual_session
        )
        analytics.calculate_analytics()
        
        return JsonResponse({
            "success": True,
            "message": "Teacher reflection saved successfully!",
            "feedback_id": str(feedback.id)
        })
        
    except Exception as e:
        logger.error(f"Error saving teacher feedback: {e}")
        return JsonResponse({"success": False, "error": "Failed to save teacher feedback"}, status=500)


@login_required
def get_feedback_status(request):
    """Get feedback status for a session"""
    try:
        session_id = request.GET.get('session_id')
        if not session_id:
            return JsonResponse({"success": False, "error": "Session ID required"}, status=400)
        
        actual_session = get_object_or_404(ActualSession, id=session_id)
        
        from .models import StudentFeedback, TeacherFeedback
        
        # Get student feedback count
        student_feedback_count = StudentFeedback.objects.filter(actual_session=actual_session).count()
        
        # Get teacher feedback status
        teacher_feedback_completed = TeacherFeedback.objects.filter(
            actual_session=actual_session,
            facilitator=request.user
        ).exists()
        
        # Generate student feedback summary HTML
        student_summary_html = ""
        if student_feedback_count > 0:
            student_feedback = StudentFeedback.objects.filter(actual_session=actual_session)
            
            # Calculate averages
            avg_rating = sum(f.session_rating for f in student_feedback) / student_feedback_count
            understanding_yes = student_feedback.filter(topic_understanding='yes').count()
            clarity_yes = student_feedback.filter(teacher_clarity='yes').count()
            
            student_summary_html = f"""
            <div class="row text-center">
                <div class="col-md-3">
                    <div class="text-primary">
                        <h4>{avg_rating:.1f}/5</h4>
                        <small>Average Rating</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-success">
                        <h4>{understanding_yes}/{student_feedback_count}</h4>
                        <small>Understood Topic</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-info">
                        <h4>{clarity_yes}/{student_feedback_count}</h4>
                        <small>Found Teacher Clear</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="text-warning">
                        <h4>{student_feedback_count}</h4>
                        <small>Total Responses</small>
                    </div>
                </div>
            </div>
            """
        
        return JsonResponse({
            "success": True,
            "student_feedback_count": student_feedback_count,
            "teacher_feedback_completed": teacher_feedback_completed,
            "student_summary_html": student_summary_html
        })
        
    except Exception as e:
        logger.error(f"Error getting feedback status: {e}")
        return JsonResponse({"success": False, "error": "Failed to get feedback status"}, status=500)
        day_content = content[start_pos:end_pos]
        
        # Cache the content for 1 hour
        cache.set(cache_key, day_content, 60 * 60)
        
        return day_content
        
    except Exception as e:
        logger.error(f"Error loading Hindi curriculum content for day {day_number}: {e}")
        return None

@login_required
def initialize_class_sessions(request):
    """Initialize 1-150 sessions for classes that don't have them"""
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")
    
    if request.method == "POST":
        try:
            # Get all class sections that don't have planned sessions
            classes_without_sessions = []
            all_classes = ClassSection.objects.all().select_related('school')
            
            for class_section in all_classes:
                session_count = PlannedSession.objects.filter(
                    class_section=class_section,
                    is_active=True
                ).count()
                
                if session_count == 0:
                    classes_without_sessions.append(class_section)
            
            if not classes_without_sessions:
                messages.info(request, "All classes already have sessions initialized.")
                return redirect("admin_dashboard")
            
            # Initialize sessions for classes that need them
            total_created = 0
            success_count = 0
            
            for class_section in classes_without_sessions:
                try:
                    with transaction.atomic():
                        # Create all 150 sessions
                        sessions_to_create = []
                        for day_number in range(1, 151):
                            session = PlannedSession(
                                class_section=class_section,
                                day_number=day_number,
                                title=f"Day {day_number} Session",
                                description=f"Session for day {day_number}",
                                sequence_position=day_number,
                                is_required=True,
                                is_active=True
                            )
                            sessions_to_create.append(session)
                        
                        # Bulk create all sessions
                        PlannedSession.objects.bulk_create(sessions_to_create)
                        total_created += 150
                        success_count += 1
                        
                        logger.info(f"Initialized 150 sessions for {class_section}")
                        
                except Exception as e:
                    logger.error(f"Error initializing sessions for {class_section}: {e}")
                    messages.warning(request, f"Failed to initialize sessions for {class_section}: {str(e)}")
            
            if success_count > 0:
                messages.success(request, f"✅ Successfully initialized {total_created} sessions for {success_count} classes.")
            
            return redirect("admin_dashboard")
            
        except Exception as e:
            logger.error(f"Error in bulk session initialization: {e}")
            messages.error(request, f"Error initializing sessions: {str(e)}")
            return redirect("admin_dashboard")
    
    # GET request - show confirmation page
    classes_without_sessions = []
    all_classes = ClassSection.objects.all().select_related('school')
    
    for class_section in all_classes:
        session_count = PlannedSession.objects.filter(
            class_section=class_section,
            is_active=True
        ).count()
        
        if session_count == 0:
            classes_without_sessions.append(class_section)
    
    return render(request, "admin/sessions/initialize_sessions.html", {
        "classes_without_sessions": classes_without_sessions,
        "total_sessions_to_create": len(classes_without_sessions) * 150
    })

def auto_create_planned_sessions_for_all_classes():
    """
    Automatically create 1-150 planned sessions for all classes that don't have them
    This ensures facilitators always have sessions to conduct
    """
    try:
        # Get all class sections
        all_classes = ClassSection.objects.all()
        
        classes_updated = 0
        total_sessions_created = 0
        
        for class_section in all_classes:
            # Check if this class already has planned sessions
            existing_count = PlannedSession.objects.filter(
                class_section=class_section,
                is_active=True
            ).count()
            
            if existing_count == 0:
                # Create all 150 sessions for this class
                try:
                    with transaction.atomic():
                        sessions_to_create = []
                        for day_number in range(1, 151):
                            session = PlannedSession(
                                class_section=class_section,
                                day_number=day_number,
                                title=f"Day {day_number} Session",
                                description=f"Session for day {day_number}",
                                sequence_position=day_number,
                                is_required=True,
                                is_active=True
                            )
                            sessions_to_create.append(session)
                        
                        # Bulk create all sessions
                        PlannedSession.objects.bulk_create(sessions_to_create)
                        classes_updated += 1
                        total_sessions_created += 150
                        
                        logger.info(f"Auto-created 150 planned sessions for {class_section}")
                        
                except Exception as e:
                    logger.error(f"Error creating planned sessions for {class_section}: {e}")
        
        if classes_updated > 0:
            logger.info(f"Auto-created {total_sessions_created} planned sessions for {classes_updated} classes")
        
        return {
            'classes_updated': classes_updated,
            'total_sessions_created': total_sessions_created
        }
        
    except Exception as e:
        logger.error(f"Error in auto_create_planned_sessions_for_all_classes: {e}")
        return {
            'classes_updated': 0,
            'total_sessions_created': 0
        }