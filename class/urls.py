from django.urls import path
from .views import (
    # Auth
    login_view, logout_view, dashboard, no_permission,

    # Admin – users & setup
    users_view, add_user, edit_user, delete_user, create_user_ajax,
    schools, add_school, edit_school, delete_school, school_detail,
    class_sections_list, class_section_add, edit_class_section, class_section_delete,
    assign_facilitator,admin_sessions_filter,

    # Admin – students
    students_list, student_add, student_edit, student_delete, student_import,

    # Sessions & attendance
    sessions_view,          # admin class sessions
    class_attendance,       # admin class attendance
    today_session,          # facilitator today session
    start_session,          # facilitator start session
    mark_attendance,        # facilitator mark attendance
    facilitator_classes,    # facilitator classes list
    facilitator_attendance, # facilitator attendance filtering
    admin_attendance_filter,
    planned_session_create,
    planned_session_edit,
    planned_session_delete,
    planned_session_import,
    bulk_delete_sessions,
    download_sample_csv,
    toggle_facilitator_assignment,
    delete_facilitator_assignment,
    
    # Curriculum Navigator
    curriculum_navigator,
    hindi_curriculum_navigator,
    facilitator_curriculum_session,
    curriculum_content_api,
    facilitator_session_quick_nav,
    
    # Facilitator Management
    facilitator_schools,
    facilitator_school_detail,
    facilitator_students_list,
    facilitator_student_detail,
    facilitator_student_edit,
    
    # Admin Curriculum Session Management
    admin_curriculum_sessions_list,
    admin_curriculum_session_create,
    admin_curriculum_session_edit,
    admin_curriculum_session_delete,
    admin_curriculum_session_preview,
    admin_sessions_overview,
    ajax_school_classes_admin,
    
    # Performance API endpoints
    api_lazy_load_sessions,
    api_lazy_load_schools,
    api_dashboard_stats,
    api_dashboard_recent_sessions,
    api_dashboard_curriculum_updates,
    api_curriculum_sessions_filter,
    
    # AJAX endpoints
    ajax_facilitator_schools,
    ajax_school_classes,
    ajax_class_students,
    debug_sessions,
)
from . import facilitator_views

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
    path("facilitator/dashboard/", facilitator_views.facilitator_dashboard, name="facilitator_dashboard"),

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
    
     path("admin/schools/<uuid:school_id>/delete/", delete_school, name="delete_school"),

    
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
    path(
    "admin/attendance/",
    admin_attendance_filter,
    name="admin_attendance_filter"
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
    path(
    "admin/sessions/",
    admin_sessions_filter,
    name="admin_sessions_filter"
),
path(
    "admin/sessions/classes/",
    admin_sessions_filter,
    name="admin_class_sessions_filter"
),





    # ======================
    # Facilitator Flow
    # ======================
    path(
        "facilitator/class/<uuid:class_section_id>/today/",
        today_session,
        name="facilitator_today_session"
    ),
    path(
        "facilitator/class/<uuid:class_section_id>/debug/",
        debug_sessions,
        name="debug_sessions"
    ),
    path(
        "facilitator/session/start/<uuid:planned_session_id>/",
        start_session,
        name="start_session"
    ),
    path(
        "facilitator/session/<uuid:actual_session_id>/attendance/",
        mark_attendance,
        name="mark_attendance"
    ),
    path(
        "facilitator/attendance/",
        facilitator_attendance,
        name="facilitator_attendance"
    ),
    
    # AJAX endpoints for attendance filtering
    path(
        "api/facilitator/schools/",
        ajax_facilitator_schools,
        name="ajax_facilitator_schools"
    ),
    path(
        "api/facilitator/classes/",
        ajax_school_classes,
        name="ajax_school_classes"
    ),
    path(
        "api/facilitator/students/",
        ajax_class_students,
        name="ajax_class_students"
    ),
    path(
        "facilitator/class/<uuid:class_section_id>/planned-session/create/",
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
path(
    "admin/classes/<uuid:class_section_id>/planned-sessions/import/",
    planned_session_import,
    name="planned_session_import"
),
path(
    "admin/classes/<uuid:class_section_id>/planned-sessions/bulk-delete/",
    bulk_delete_sessions,
    name="bulk_delete_sessions"
),
path(
    "admin/download-sample-csv/",
    download_sample_csv,
    name="download_sample_csv"
),
path(
    "admin/facilitator-assignment/<uuid:assignment_id>/toggle/",
    toggle_facilitator_assignment,
    name="toggle_facilitator_assignment"
),
path(
    "admin/facilitator-assignment/<uuid:assignment_id>/delete/",
    delete_facilitator_assignment,
    name="delete_facilitator_assignment"
),


    # ======================
    # No Permission
    # ======================
    path("no_permission/", no_permission, name="no_permission"),
    
    # ======================
    # Curriculum Navigator
    # ======================
    path("curriculum/", curriculum_navigator, name="curriculum_navigator"),
    path("curriculum/hindi/", hindi_curriculum_navigator, name="hindi_curriculum_navigator"),
    path(
        "facilitator/class/<uuid:class_section_id>/curriculum/",
        facilitator_curriculum_session,
        name="facilitator_curriculum_session"
    ),
    path("api/curriculum/content/", curriculum_content_api, name="curriculum_content_api"),
    path(
        "api/facilitator/class/<uuid:class_section_id>/sessions/",
        facilitator_session_quick_nav,
        name="facilitator_session_quick_nav"
    ),
    
    # ======================
    # Facilitator Management
    # ======================
    path("facilitator/schools/", facilitator_schools, name="facilitator_schools"),
    path(
        "facilitator/school/<uuid:school_id>/",
        facilitator_school_detail,
        name="facilitator_school_detail"
    ),
    path(
        "facilitator/class/<uuid:class_section_id>/students/",
        facilitator_students_list,
        name="facilitator_students_list"
    ),
    path(
        "facilitator/class/<uuid:class_section_id>/student/<uuid:student_id>/",
        facilitator_student_detail,
        name="facilitator_student_detail"
    ),
    path(
        "facilitator/class/<uuid:class_section_id>/student/<uuid:student_id>/edit/",
        facilitator_student_edit,
        name="facilitator_student_edit"
    ),
    
    # ======================
    # AJAX endpoints
    # ======================
    path("api/school-classes/", ajax_school_classes_admin, name="ajax_school_classes_admin"),
    
    # ======================
    # Admin Sessions Overview
    # ======================
    path("admin/sessions/overview/", admin_sessions_overview, name="admin_sessions_overview"),
    
    # ======================
    # Admin Curriculum Session Management
    # ======================
    path("admin/curriculum-sessions/", admin_curriculum_sessions_list, name="admin_curriculum_sessions_list"),
    path("admin/curriculum-sessions/create/", admin_curriculum_session_create, name="admin_curriculum_session_create"),
    path("admin/curriculum-sessions/<uuid:session_id>/edit/", admin_curriculum_session_edit, name="admin_curriculum_session_edit"),
    path("admin/curriculum-sessions/<uuid:session_id>/delete/", admin_curriculum_session_delete, name="admin_curriculum_session_delete"),
    path("admin/curriculum-sessions/<uuid:session_id>/preview/", admin_curriculum_session_preview, name="admin_curriculum_session_preview"),
    
    # ======================
    # Facilitator Student Management (New)
    # ======================
    path("facilitator/my-schools/", facilitator_views.FacilitatorSchoolListView.as_view(), name="facilitator_schools_list"),
    path("facilitator/my-schools/<uuid:pk>/", facilitator_views.FacilitatorSchoolDetailView.as_view(), name="facilitator_school_detail"),
    path("facilitator/students/", facilitator_views.FacilitatorStudentListView.as_view(), name="facilitator_students_list"),
    path("facilitator/students/create/", facilitator_views.FacilitatorStudentCreateView.as_view(), name="facilitator_student_create"),
    path("facilitator/students/<uuid:pk>/edit/", facilitator_views.FacilitatorStudentUpdateView.as_view(), name="facilitator_student_edit"),
    path("facilitator/students/<uuid:student_id>/detail/", facilitator_views.facilitator_student_detail, name="facilitator_student_detail"),
    path("facilitator/ajax/school-classes/", facilitator_views.facilitator_ajax_school_classes, name="facilitator_ajax_school_classes"),
    path("facilitator/debug/schools/", facilitator_views.facilitator_debug_schools, name="facilitator_debug_schools"),
    path("facilitator/test/access/", facilitator_views.facilitator_test_access, name="facilitator_test_access"),
    
    # ======================
    # Performance API Endpoints
    # ======================
    path("api/lazy-load/sessions/", api_lazy_load_sessions, name="api_lazy_load_sessions"),
    path("api/lazy-load/schools/", api_lazy_load_schools, name="api_lazy_load_schools"),
    path("api/dashboard/stats/", api_dashboard_stats, name="api_dashboard_stats"),
    path("api/dashboard/recent-sessions/", api_dashboard_recent_sessions, name="api_dashboard_recent_sessions"),
    path("api/dashboard/curriculum-updates/", api_dashboard_curriculum_updates, name="api_dashboard_curriculum_updates"),
    path("api/curriculum-sessions/filter/", api_curriculum_sessions_filter, name="api_curriculum_sessions_filter"),
]
