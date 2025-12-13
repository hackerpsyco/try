from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import AddUserForm, EditUserForm, AddSchoolForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model



User = get_user_model()

from django.views.decorators.csrf import csrf_exempt
from .models import User, Role, School  # adjust imports

@csrf_exempt  # remove this if you handle CSRF in headers correctly
def create_user_ajax(request):
    if request.method == "POST":
        try:
            full_name = request.POST.get("full_name")
            email = request.POST.get("email")
            password = request.POST.get("password")
            role_id = request.POST.get("role")

            if not all([full_name, email, password, role_id]):
                return JsonResponse({"success": False, "error": "All fields are required."})

            # Check if user exists
            if User.objects.filter(email=email).exists():
                return JsonResponse({"success": False, "error": "User with this email already exists."})

            # Create user
            role = Role.objects.get(id=role_id)
            user = User.objects.create(full_name=full_name, email=email, role=role)
            user.set_password(password)
            user.save()

            # Return user info for table update
            return JsonResponse({
                "success": True,
                "user": {
                    "id": str(user.id),
                    "full_name": user.full_name,
                    "email": user.email,
                    "role_name": user.role.name
                }
            })

        except Role.DoesNotExist:
            return JsonResponse({"success": False, "error": "Invalid role selected."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})

# Mapping roles to their dashboard URLs and templates
ROLE_CONFIG = {
    "ADMIN": {"url": "/admin/dashboard/", "template": "admin/dashboard.html"},
    "SUPERVISOR": {"url": "/supervisor/dashboard/", "template": "Supervisor/dashboard.html"},
    "FACILITATOR": {"url": "/facilitator/dashboard/", "template": "Facilitator/dashboard.html"},
}

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)

            # Get the role name and redirect
            role_name = user.role.name.upper()
            role_config = ROLE_CONFIG.get(role_name)
            redirect_url = role_config["url"] if role_config else "/" # Safely get URL
            return redirect(redirect_url)
        else:
            messages.error(request, "Invalid email or password")

    return render(request, "auth/login.html")


@login_required
def dashboard(request):
    role_name = request.user.role.name.upper()
    role_config = ROLE_CONFIG.get(role_name)

    if not role_config:
        messages.error(request, "Invalid role configuration or insufficient permissions.")
        return redirect("no_permission")

    dashboard_template = role_config["template"]
    context = {}

    # Only fetch users and roles if it\"s the admin dashboard
    if role_name == "ADMIN":
        users = User.objects.all().order_by("-created_at")
        roles = Role.objects.all()
        context = {
            "users": users,
            "roles": roles,
        }

    return render(
        request,
        dashboard_template,
        context
    )




@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect("login")


def user_list(request):
    if request.user.role.id != 0:
        return redirect("no_permission")

    users = User.objects.all().order_by("-created_at")
    return render(request, "admin/dashboard.html", {"users": users})
def add_user(request):
    if request.user.role.id != 0:
        return redirect("no_permission")

    if request.method == "POST":
        form = AddUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()

            messages.success(request, "User created successfully!")
            return redirect("user_list")
    else:
        form = AddUserForm()

    return render(request, "admin/add_user.html", {"form": form})
def edit_user(request, user_id):
    if request.user.role.id != 0:
        return redirect("no_permission")

    user = get_object_or_404(User, id=user_id)
    form = EditUserForm(instance=user)

    if request.method == "POST":
        form = EditUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully!")
            return redirect("user_list")

    return render(request, "admin/edit_user.html", {"form": form, "user": user})
def delete_user(request, user_id):
    if request.user.role.id != 0:
        return redirect("no_permission")

    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, "User deleted successfully!")
    return redirect("user_list")

def no_permission(request):
    return render(request, "no_permission.html")

# New School Management Views
@login_required
def school_list(request):
    # Ensure only Admin can access this view
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to view schools.")
        return redirect("no_permission")

    schools = School.objects.all().order_by("-created_at")
    context = {"schools": schools}
    return render(request, "admin/school_list.html", context)

@login_required
def add_school(request):
    # Ensure only Admin can access this view
    if request.user.role.name.upper() != "ADMIN":
        messages.error(request, "You do not have permission to add schools.")
        return redirect("no_permission")

    if request.method == "POST":
        form = AddSchoolForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "School added successfully!")
            return redirect("school_list")  # Redirect to the school list view
    else:
        form = AddSchoolForm()

    context = {"form": form}
    return render(request, "admin/add_school.html", context)
