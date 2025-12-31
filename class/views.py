import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.urls import reverse
import csv
import openpyxl
from .forms import AddUserForm, EditUserForm, AddSchoolForm, ClassSectionForm, AssignFacilitatorForm
from .models import User, Role, School, ClassSection, FacilitatorSchool,Student,Enrollment,PlannedSession, ActualSession, Attendance
from datetime import date
from django.db.models import Max
from django.db.models import Exists, OuterRef
import re



User = get_user_model()

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
def schools(request):
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to view schools.")
        return redirect("no_permission")

    schools = School.objects.all().order_by("-created_at")
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
        .prefetch_related('actual_sessions')
        .order_by("day_number")
    )

    # Add status information to each planned session
    for ps in planned_sessions:
        ps.status_info = "pending"
        ps.status_class = "secondary"
        
        if ps.is_conducted:
            ps.status_info = "completed"
            ps.status_class = "success"
        else:
            # Check for holiday/cancelled status
            actual_session = ps.actual_sessions.first()
            if actual_session:
                if actual_session.status == "holiday":
                    ps.status_info = "holiday"
                    ps.status_class = "warning"
                elif actual_session.status == "cancelled":
                    ps.status_info = "cancelled"
                    ps.status_class = "danger"

    # ✅ next pending session (FIRST not conducted)
    next_pending = next(
        (ps for ps in planned_sessions if not ps.is_conducted and ps.status_info == "pending"),
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


@login_required
def today_session(request, class_section_id):
    class_section = get_object_or_404(ClassSection, id=class_section_id)

    # NEW LOGIC: Show sessions in this priority order:
    # 1. First truly pending session (no ActualSession record)
    # 2. If no pending sessions, show the most recent holiday/cancelled session
    # 3. If all sessions are conducted, show "completed"
    
    # First, try to find a truly pending session
    pending_session = PlannedSession.objects.filter(
        class_section=class_section,
        is_active=True,
        actual_sessions__isnull=True  # No ActualSession record at all
    ).order_by("day_number").first()
    
    planned_session = None
    session_status = None
    
    if pending_session:
        # Found a pending session - show it
        planned_session = pending_session
        session_status = "pending"
    else:
        # No pending sessions - check for recent holiday/cancelled sessions
        recent_non_conducted = PlannedSession.objects.filter(
            class_section=class_section,
            is_active=True,
            actual_sessions__status__in=['holiday', 'cancelled']
        ).order_by("-actual_sessions__date").first()
        
        if recent_non_conducted:
            # Show the most recent holiday/cancelled session
            planned_session = recent_non_conducted
            actual_session = recent_non_conducted.actual_sessions.first()
            session_status = actual_session.status
        # If no holiday/cancelled sessions either, planned_session stays None (all completed)

    video_id = None
    if planned_session and planned_session.youtube_url:
        video_id = extract_youtube_id(planned_session.youtube_url)

    return render(request, "facilitator/Today_session.html", {
        "class_section": class_section,
        "planned_session": planned_session,
        "session_status": session_status,
        "video_id": video_id,
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

    # Read status from POST request, default to "conducted"
    status = request.POST.get('status', 'conducted')
    remarks = request.POST.get('remarks', '')

    actual_session, created = ActualSession.objects.get_or_create(
        planned_session=planned,
        date=timezone.now().date(),
        defaults={
            "facilitator": request.user,
            "status": status,
            "remarks": remarks
        }
    )

    # If session already exists, update it (in case of status change)
    if not created:
        actual_session.status = status
        actual_session.remarks = remarks
        actual_session.save()

    # Redirect based on status
    if status == "conducted":
        return redirect("mark_attendance", actual_session.id)
    else:
        # For holiday/cancelled sessions, redirect back to facilitator classes
        messages.success(request, f"Session marked as {status}.")
        return redirect("facilitator_classes")
@login_required
def mark_attendance(request, actual_session_id):
    if request.user.role.name.upper() != "FACILITATOR":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    session = get_object_or_404(ActualSession, id=actual_session_id)

    enrollments = Enrollment.objects.filter(
        class_section=session.planned_session.class_section,
        is_active=True
    ).select_related("student")

    if request.method == "POST":
        for enrollment in enrollments:
            status = request.POST.get(str(enrollment.id))
            if status:
                Attendance.objects.update_or_create(
                    actual_session=session,
                    enrollment=enrollment,
                    defaults={"status": status}
                )

        messages.success(request, "Attendance saved successfully.")
        return redirect(
            "class_attendance",
            class_section_id=session.planned_session.class_section.id
        )

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

    # Debug: Check current user details
    messages.info(request, f"Debug: Current user: {request.user.full_name} ({request.user.email}), Role: {request.user.role.name}")

    # Get facilitator's assigned schools with debugging
    assigned_schools = FacilitatorSchool.objects.filter(
        facilitator=request.user,
        is_active=True
    ).select_related("school")

    # Debug: Check query results
    messages.info(request, f"Debug: Found {assigned_schools.count()} school assignments")
    for fs in assigned_schools:
        messages.info(request, f"Debug: Assigned to {fs.school.name} (Active: {fs.is_active})")

    # Also check ALL FacilitatorSchool records for this user (including inactive)
    all_assignments = FacilitatorSchool.objects.filter(
        facilitator=request.user
    ).select_related("school")
    
    messages.info(request, f"Debug: Total assignments (including inactive): {all_assignments.count()}")
    for fs in all_assignments:
        messages.info(request, f"Debug: {fs.school.name} - Active: {fs.is_active}, Created: {fs.created_at}")

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
    """Import planned sessions from CSV/Excel file"""
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    class_section = get_object_or_404(ClassSection, id=class_section_id)

    if request.method == "POST":
        file = request.FILES.get("file")

        if not file:
            messages.error(request, "Please upload a file")
            return redirect(request.path)

        ext = file.name.split(".")[-1].lower()

        # Read file based on extension
        if ext == "csv":
            # Try different encodings to handle various CSV formats
            file_content = file.read()
            
            # Try UTF-8 first, then fallback to other common encodings
            for encoding in ['utf-8', 'utf-8-sig', 'windows-1252', 'iso-8859-1', 'cp1252']:
                try:
                    decoded_content = file_content.decode(encoding)
                    rows = csv.DictReader(decoded_content.splitlines())
                    # Convert to list to process
                    rows = list(rows)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                messages.error(request, "Unable to decode the CSV file. Please ensure it's saved in UTF-8 format.")
                return redirect(request.path)
        elif ext in ["xlsx", "xls"]:
            try:
                wb = openpyxl.load_workbook(file)
                sheet = wb.active
                headers = [str(cell.value).strip() if cell.value else "" for cell in sheet[1]]
                rows = []
                for r in sheet.iter_rows(min_row=2, values_only=True):
                    # Handle None values in Excel cells
                    row_data = [str(cell) if cell is not None else "" for cell in r]
                    rows.append(dict(zip(headers, row_data)))
            except Exception as e:
                messages.error(request, f"Error reading Excel file: {str(e)}")
                return redirect(request.path)
        else:
            messages.error(request, "Unsupported file format. Please use CSV or Excel files.")
            return redirect(request.path)

        created_count = 0
        skipped_count = 0

        # Get the highest day number for this class section
        last_day = PlannedSession.objects.filter(
            class_section=class_section
        ).aggregate(Max("day_number"))["day_number__max"] or 0

        # Process rows
        for row_index, row in enumerate(rows, start=2):  # Start from 2 for Excel row numbering
            try:
                # Handle different data types and None values
                day_number = row.get("day_number", "")
                topic = str(row.get("topic", "")).strip()
                youtube_url = str(row.get("youtube_url", "")).strip()
                description = str(row.get("description", "")).strip()

                # Skip empty rows
                if not any([topic, youtube_url, description]):
                    continue

                # Basic validation
                if not topic:
                    skipped_count += 1
                    continue

                # Handle day_number - if not provided, auto-increment
                if day_number and str(day_number).strip():
                    try:
                        day_number = int(float(str(day_number).strip()))  # Handle Excel decimal numbers
                    except (ValueError, TypeError):
                        last_day += 1
                        day_number = last_day
                else:
                    last_day += 1
                    day_number = last_day

                # Check if session with this day number already exists
                if PlannedSession.objects.filter(
                    class_section=class_section,
                    day_number=day_number
                ).exists():
                    skipped_count += 1
                    continue

                # Create planned session
                PlannedSession.objects.create(
                    class_section=class_section,
                    day_number=day_number,
                    topic=topic,
                    youtube_url=youtube_url or "",
                    description=description
                )
                created_count += 1
                
            except Exception as e:
                # Log the error and skip this row
                skipped_count += 1
                continue

        # User feedback
        if created_count == 0:
            messages.warning(
                request,
                f"No sessions imported. Skipped rows: {skipped_count}"
            )
        else:
            messages.success(
                request,
                f"{created_count} sessions imported successfully "
                f"(Skipped: {skipped_count})"
            )

        return redirect("admin_class_sessions", class_section.id)

    return render(request, "admin/classes/planned_session_import.html", {
        "class_section": class_section
    })


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


