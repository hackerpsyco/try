from django.urls import path
from .views import (
    login_view, logout_view, dashboard,
    users_view, add_user, edit_user, delete_user, create_user_ajax,
    schools, add_school, edit_school, school_detail,
    class_sections_list, class_section_add, class_section_delete,
    no_permission,edit_class_section, assign_facilitator
)

urlpatterns = [
    # ----------------------
    # Authentication
    # ----------------------
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # ----------------------
    # Dashboards
    # ----------------------
    path("admin/dashboard/", dashboard, name="admin_dashboard"),
    path("supervisor/dashboard/", dashboard, name="supervisor_dashboard"),
    path("facilitator/dashboard/", dashboard, name="facilitator_dashboard"),

    # ----------------------
    # Users (Admin)
    # ----------------------
    path("admin/users/", users_view, name="users_view"),
    path("admin/users/add/", add_user, name="add_user"),
    path("admin/users/edit/<uuid:user_id>/", edit_user, name="edit_user"),
    path("admin/users/delete/<uuid:user_id>/", delete_user, name="delete_user"),
    path("admin/users/create-ajax/", create_user_ajax, name="create_user_ajax"),

    # ----------------------
    # Schools (Admin)
    # ----------------------
    path("admin/schools/", schools, name="schools"),
    path("admin/schools/add/", add_school, name="add_school"),
    path("admin/schools/edit/<uuid:school_id>/", edit_school, name="edit_school"),
    path("admin/schools/<uuid:school_id>/", school_detail, name="school_detail"),

    # ----------------------
    # Classes (Admin)
    # ----------------------
    path(
        "admin/classes/",
        class_sections_list,
        name="class_sections_list"
    ),
    path(
        "admin/schools/<uuid:school_id>/classes/",
        class_sections_list,
        name="class_sections_list_by_school"
    ),
    path(
        "admin/schools/<uuid:school_id>/classes/add/",
        class_section_add,
        name="class_section_add"
    ),
    path(
        "admin/classes/edit/<uuid:pk>/",
        edit_class_section,
        name="edit_class_section"
        ),
      path(
        "admin/classes/delete/<uuid:pk>/",
        class_section_delete,
        name="class_section_delete"
    ),

    # ----------------------
    # No Permission
    # ----------------------
    path("no_permission/", no_permission, name="no_permission"),

]
