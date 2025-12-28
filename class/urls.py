from django.urls import path
from .views import (
    # Auth
    login_view, logout_view, dashboard, no_permission,

    # Admin – users & setup
    users_view, add_user, edit_user, delete_user, create_user_ajax,
    schools, add_school, edit_school, school_detail,
    class_sections_list, class_section_add, edit_class_section, class_section_delete,
    assign_facilitator,

    # Admin – students
    students_list, student_add, student_edit, student_delete, student_import,

    # Sessions & attendance
    sessions_view,          # admin class sessions
    class_attendance,       # admin class attendance
    today_session,          # facilitator today session
    start_session,          # facilitator start session
    mark_attendance,        # facilitator mark attendance
    facilitator_classes,    # facilitator classes list
    planned_session_create,
    planned_session_edit,
    planned_session_delete,
)

urlpatterns = [

    # ======================
    # Authentication
    # ======================
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # ======================
    # Dashboards (role based)
    # ======================
    path("admin/dashboard/", dashboard, name="admin_dashboard"),
    path("supervisor/dashboard/", dashboard, name="supervisor_dashboard"),
    path("facilitator/dashboard/", dashboard, name="facilitator_dashboard"),

    # ======================
    # Users (ADMIN)
    # ======================
    path("admin/users/", users_view, name="users_view"),
    path("admin/users/add/", add_user, name="add_user"),
    path("admin/users/edit/<uuid:user_id>/", edit_user, name="edit_user"),
    path("admin/users/delete/<uuid:user_id>/", delete_user, name="delete_user"),
    path("admin/users/create-ajax/", create_user_ajax, name="create_user_ajax"),

    # ======================
    # Schools (ADMIN)
    # ======================
    path("admin/schools/", schools, name="schools"),
    path("admin/schools/add/", add_school, name="add_school"),
    path("admin/schools/edit/<uuid:school_id>/", edit_school, name="edit_school"),
    path("admin/schools/<uuid:school_id>/", school_detail, name="school_detail"),

    # ======================
    # Classes (ADMIN)
    # ======================
    path("admin/classes/", class_sections_list, name="class_sections_list"),
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

    # ======================
    # Students (ADMIN)
    # ======================
    path(
        "admin/schools/<uuid:school_id>/students/",
        students_list,
        name="students_list"
    ),
    path(
        "admin/schools/<uuid:school_id>/students/add/",
        student_add,
        name="student_add"
    ),
    path(
        "admin/schools/<uuid:school_id>/students/<uuid:student_id>/edit/",
        student_edit,
        name="student_edit"
    ),
    path(
        "admin/schools/<uuid:school_id>/students/<uuid:student_id>/delete/",
        student_delete,
        name="student_delete"
    ),
    path(
        "admin/schools/<uuid:school_id>/students/import/",
        student_import,
        name="student_import"
    ),

    # ======================
    # Facilitator Assignment (ADMIN)
    # ======================
    path(
        "admin/classes/<uuid:class_section_id>/assign-facilitator/",
        assign_facilitator,
        name="assign_facilitator"
    ),

    # ======================
    # Sessions & Attendance (ADMIN – READ ONLY)
    # ======================
    path(
        "admin/classes/<uuid:class_section_id>/sessions/",
        sessions_view,
        name="admin_class_sessions"
    ),
    path(
        "admin/classes/<uuid:class_section_id>/attendance/",
        class_attendance,
        name="class_attendance"
    ),
    path(
    "Facilitator/classes/",
    facilitator_classes,
    name="facilitator_classes"
),


    # ======================
    # Facilitator Flow
    # ======================
    path(
        "Facilitator/class/<uuid:class_section_id>/today/",
        today_session,
        name="facilitator_today_session"
    ),
    path(
        "Facilitator/session/start/<uuid:planned_session_id>/",
        start_session,
        name="start_session"
    ),
    path(
        "Facilitator/session/<uuid:actual_session_id>/attendance/",
        mark_attendance,
        name="mark_attendance"
    ),
    path(
        "Facilitator/class/<uuid:class_section_id>/planned-session/create/",
        planned_session_create,
        name="planned_session_create"
    ),
   path(
    "admin/planned-session/<uuid:session_id>/edit/",
    planned_session_edit,
    name="planned_session_edit"
),
path(
    "admin/planned-session/<uuid:session_id>/delete/",
    planned_session_delete,
    name="planned_session_delete"
),


    # ======================
    # No Permission
    # ======================
    path("no_permission/", no_permission, name="no_permission"),
]
