import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
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
                role_id=role.id
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

    return render(request, "admin/schools/detail.html", {
        "school": school,
        "class_sections": classes
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
        .order_by("day_number")
    )

    # ✅ next pending session (FIRST not conducted)
    next_pending = next(
        (ps for ps in planned_sessions if not ps.is_conducted),
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

    planned_session = PlannedSession.objects.filter(
        class_section=class_section,
        is_active=True
    ).exclude(
        actual_sessions__status="conducted"
    ).order_by("day_number").first()

    video_id = None
    if planned_session and planned_session.youtube_url:
        video_id = extract_youtube_id(planned_session.youtube_url)

    return render(request, "facilitator/Today_session.html", {
        "class_section": class_section,
        "planned_session": planned_session,
        "video_id": video_id,
    })

from django.utils import timezone

@login_required
def start_session(request, planned_session_id):
    if request.user.role.name.upper() != "FACILITATOR":
        messages.error(request, "Permission denied.")
        return redirect("no_permission")

    planned = get_object_or_404(PlannedSession, id=planned_session_id)

    actual_session, _ = ActualSession.objects.get_or_create(
        planned_session=planned,
        date=timezone.now().date(),
        defaults={
            "facilitator": request.user,
            "status": "conducted"
        }
    )

    return redirect("mark_attendance", actual_session.id)


    return redirect("mark_attendance", actual_session.id)
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

    # 🔒 Safety check: already conducted?
    if planned.actual_sessions.filter(status="conducted").exists():
        messages.error(
            request,
            "This session has already been conducted and cannot be deleted."
        )
        return redirect("admin_class_sessions", class_section.id)

    if request.method == "POST":
        planned.delete()
        messages.success(request, "Planned session deleted.")
        return redirect("admin_class_sessions", class_section.id)

    # Optional confirm page
    return render(request, "admin/classes/planned_session_confirm_delete.html", {
        "planned_session": planned,
        "class_section": class_section,
        
    })


