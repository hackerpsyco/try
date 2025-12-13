from django.urls import path
from .views import login_view, dashboard, logout_view, user_list, add_user, edit_user, delete_user, create_user_ajax, no_permission, school_list, add_school

urlpatterns = [
    path("", login_view, name="login"),
    path("facilitator/dashboard/", dashboard, name="facilitator_dashboard"),
    path("supervisor/dashboard/", dashboard, name="supervisor_dashboard"),
    path("admin/dashboard/", dashboard, name="admin_dashboard"),
    path("logout/", logout_view, name="logout"),
    path("list/", user_list, name="user_list"),
    path("add/", add_user, name="add_user"),
    path("edit/<uuid:user_id>/", edit_user, name="edit_user"),
    path("delete/<uuid:user_id>/", delete_user, name="delete_user"),
    path("create-ajax/", create_user_ajax, name="create-ajax"),
    path("no_permission/", no_permission, name="no_permission"),

    # School Management URLs
    path("schools/", school_list, name="school_list"),
    path("schools/add/", add_school, name="add_school"),
]
