
from django.urls import path
from .views import (
    login_view, logout_view, dashboard,
    users_view, add_user, edit_user, delete_user, create_user_ajax,
    schools, add_school, edit_school, class_view, no_permission
)

urlpatterns = [
    # Auth
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # Dashboards
    path("admin/dashboard/", dashboard, name="admin_dashboard"),
    path("supervisor/dashboard/", dashboard, name="supervisor_dashboard"),
    path("facilitator/dashboard/", dashboard, name="facilitator_dashboard"),

    # Users
    path("users/", users_view, name="users_view"),
    path("users/add/", add_user, name="add_user"),
    path("users/edit/<uuid:user_id>/", edit_user, name="edit_user"),
    path("users/delete/<uuid:user_id>/", delete_user, name="delete_user"),
    path("users/create-ajax/", create_user_ajax, name="create_user_ajax"),

    # Schools
    path("schools/", schools, name="schools"),
    path("schools/add/", add_school, name="add_school"),
    path("schools/edit/<uuid:school_id>/", edit_school, name="edit_school"),

    # Classes
    path("class/", class_view, name="class_view"),
    path("class/<uuid:school_id>/", class_view, name="class_view_by_school"),

    # No Permission
    path("no_permission/", no_permission, name="no_permission"),
]
