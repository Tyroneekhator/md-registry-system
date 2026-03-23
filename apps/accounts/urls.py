from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),

    path("users/", views.users_list_view, name="users_list"),
    path("users/create/", views.user_create_view, name="user_create"),
    path("users/<int:user_id>/edit/", views.user_edit_view, name="user_edit"),
    path("users/<int:user_id>/toggle-active/", views.user_disable_view, name="user_disable"),
    path("users/<int:user_id>/", views.user_detail_view, name="user_detail"),

    path("groups/", views.groups_list_view, name="groups_list"),
    path("groups/<int:group_id>/permissions/", views.group_permissions_view, name="group_permissions"),

    path("access-denied/", views.access_denied_view, name="access_denied"),
]
