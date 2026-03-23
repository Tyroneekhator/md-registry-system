from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q


from django.contrib.auth.hashers import check_password, make_password

# --- Import your models (adjust names/paths if yours differ) ---
from apps.accounts.models import (
    Users, Groups, Permissions, UserGroups, GroupPermissions
)

from apps.workflow.models import AuditLogs


# --- Normalizers: expose Django-friendly attribute names for templates ---
def _norm_user(u: Users):
    if not u:
        return u

    u.user_id = u.UserID
    u.username = u.Username
    u.is_active = u.IsActive

    if not hasattr(u, "full_name"):
        u.full_name = getattr(u, "FullName", "") if hasattr(u, "FullName") else ""
    if not hasattr(u, "email"):
        u.email = getattr(u, "Email", "") if hasattr(u, "Email") else ""

    return u

def _norm_group(g: Groups):
    if not g:
        return g
    g.group_id = g.GroupID
    g.name = g.GroupName
    
    
    # ✅ FIX: add descriptions (since Groups table has no Description column)
    role_descriptions = {
        "Admin": "Full system access: users, roles, restore deleted records, audit oversight.",
        "Clerk": "Can create/edit records, upload attachments, and perform day-to-day registry operations.",
        "Viewer": "Read-only access: can view records and dashboards but cannot modify data.",
    }
    g.description = role_descriptions.get(g.name, "")
    
    return g


def _norm_permission(p: Permissions):
    if not p:
        return p
    p.id = p.PermissionID
    p.code = p.PermissionCode
    # ✅ FIX: template-friendly aliases
    p.name = p.PermissionCode
    p.description = p.Description
    return p


# ----------------------------
# Helpers / Decorators
# ----------------------------
def _get_current_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    try:
        return _norm_user(Users.objects.get(UserID=user_id, IsActive=True))
    except Users.DoesNotExist:
        return None


def _get_user_groups(user: Users):
    """
    Returns a queryset of Groups the user belongs to.

    FIX:
    - Old code used: usergroup__user (doesn't exist)
    - Correct related query name for UserGroups -> Groups is: usergroups
      and the FK field on UserGroups to Users is: UserID (not user). :contentReference[oaicite:5]{index=5}
    """
    return Groups.objects.filter(usergroups__UserID=user).distinct()


def _is_admin(user: Users) -> bool:
    if not user:
        return False
    return _get_user_groups(user).filter(GroupName__iexact="Admin").exists()


def _is_clerk(user: Users) -> bool:
    if not user:
        return False
    return _get_user_groups(user).filter(GroupName__iexact="Clerk").exists()


def login_required_view(view_func):
    def wrapper(request, *args, **kwargs):
        user = _get_current_user(request)
        if not user:
            return redirect("accounts:login")
        request.current_user = user  # attach for convenience
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required_view(view_func):
    def wrapper(request, *args, **kwargs):
        user = _get_current_user(request)
        if not user:
            return redirect("accounts:login")
        if not _is_admin(user):
            return redirect("accounts:access_denied")
        request.current_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def _audit(request, event_type: str, details: str = ""):
    """
    Schema-aligned audit log write:
    AuditLogs(EventType, ActorUserID, Details, EventTime)
    """
    user = _get_current_user(request)
    try:
        AuditLogs.objects.create(
            EventType=event_type,
            ActorUserID=user,
            Details=details,
            EventTime=timezone.now(),
        )
    except Exception:
        # Don’t block login/logout if auditing fails
        pass


# ----------------------------
# 1) login_view
# ----------------------------
def login_view(request):
    if request.method == "GET":
        return render(request, "accounts/login.html")

    # POST
    username = (request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""

    if not username or not password:
        messages.error(request, "Username and password are required.")
        return redirect("accounts:login")

    try:
        user = _norm_user(Users.objects.get(Username__iexact=username))
    except Users.DoesNotExist:
        messages.error(request, "Invalid login credentials.")
        return redirect("accounts:login")

    if not getattr(user, "is_active", True):
        messages.error(request, "Your account is disabled. Contact an Admin.")
        return redirect("accounts:login")

    if not check_password(password, user.PasswordHash):
        messages.error(request, "Invalid login credentials.")
        return redirect("accounts:login")

    # Start session
    request.session["user_id"] = user.UserID
    request.session["username"] = user.Username

    _audit(request, event_type="LOGIN", details=f"User {user.Username} logged in.")

    return redirect("records:dashboard")


# ----------------------------
# 2) logout_view
# ----------------------------
@login_required_view
def logout_view(request):
    user = request.current_user

    _audit(request, event_type="LOGOUT", details=f"User {user.username} logged out.")

    request.session.flush()
    return redirect("accounts:login")


# ----------------------------
# 3) profile_view
# ----------------------------
@login_required_view
def profile_view(request):
    user = request.current_user
    groups = [_norm_group(g) for g in _get_user_groups(user)]

    context = {
        "user_obj": user,
        "groups": groups,
        "is_admin": _is_admin(user),
    }
    return render(request, "accounts/profile.html", context)


# ----------------------------
# 10) access_denied_view
# ----------------------------
def access_denied_view(request):
    return render(request, "accounts/access_denied.html")


# ----------------------------
# 4) users_list_view (Admin)
# ----------------------------
@login_required_view
def users_list_view(request):
    current_user = request.current_user
    
    if not (_is_admin(current_user) or _is_clerk(current_user)):
        return redirect("accounts:access_denied")
    
    q = (request.GET.get("q") or "").strip()

    # Keep as QuerySet (do NOT convert to list before filtering)
    qs = Users.objects.all().order_by("Username")

    if q:
        # Your model only guarantees Username. We'll search that, and optionally other fields if they exist.
        filters = Q(Username__icontains=q)
        if hasattr(Users, "FullName"):
            filters |= Q(FullName__icontains=q)
        if hasattr(Users, "Email"):
            filters |= Q(Email__icontains=q)
        qs = qs.filter(filters)

    users_with_groups = []
    for u in qs:
        u = _norm_user(u)
        groups = [_norm_group(g) for g in _get_user_groups(u)]
        users_with_groups.append({
            "user": u,
            "groups": groups,
        })

    return render(request, "accounts/users_list.html", {
        "q": q,
        "users_with_groups": users_with_groups,
        "is_admin": _is_admin(current_user),
        "is_clerk": _is_clerk(current_user),
    })


@login_required_view
def user_detail_view(request, user_id: int):
    current_user = request.current_user

    if not (_is_admin(current_user) or _is_clerk(current_user)):
        return redirect("accounts:access_denied")

    viewed_user = get_object_or_404(Users, UserID=user_id)
    viewed_user = _norm_user(viewed_user)
    groups = [_norm_group(g) for g in _get_user_groups(viewed_user)]

    return render(request, "accounts/user_detail.html", {
        "viewed_user": viewed_user,
        "groups": groups,
        "is_admin": _is_admin(current_user),
        "is_clerk": _is_clerk(current_user),
    })
    
# ----------------------------
# 5) user_create_view (Admin)
# ----------------------------
@admin_required_view
def user_create_view(request):
    
    current_user = request.current_user
    
    if request.method == "GET":
        return render(request, "accounts/user_form.html", {
            "mode": "create",
            "groups": [_norm_group(g) for g in Groups.objects.all().order_by("GroupName")],
            "is_admin": _is_admin(current_user),
            "is_clerk": _is_clerk(current_user),
        })

    full_name = (request.POST.get("full_name") or "").strip()
    username = (request.POST.get("username") or "").strip()
    email = (request.POST.get("email") or "").strip()
    password = (request.POST.get("password") or "").strip()
    confirm_password = (request.POST.get("confirm_password") or "").strip()
    group_id = (request.POST.get("group_id") or "").strip()

    if not username or not password:
        messages.error(request, "Username and password are required.")
        return redirect("accounts:user_create")
    
    if password != confirm_password:
        messages.error(request, "Passwords do not match.")
        return redirect("accounts:user_create")
    
    if not group_id:
        messages.error(request, "A role is required.")
        return redirect("accounts:user_create")
    
    try:
        group_id_int = int(group_id)
    except ValueError:
        messages.error(request, "Invalid role selected.")
        return redirect("accounts:user_create")

    if Users.objects.filter(Username__iexact=username).exists():
        messages.error(request, "Username already exists.")
        return redirect("accounts:user_create")
    
    user = Users.objects.create(
        Username=username,
        Email=email or None,
        PasswordHash=make_password(password),
        IsActive=True,
    )

    if hasattr(user, "FullName"):
        user.FullName = full_name
        user.save(update_fields=["FullName"])
    
    UserGroups.objects.create(UserID=user, GroupID_id=group_id_int)

    # =========================================================
    # FIXED: _audit(request, event_type, details)
    # =========================================================
    _audit(
        request,
        "USER_CREATE",
        f"Created user UserID={user.UserID} Username={user.Username}",
    )
    
    messages.success(request, "User created successfully.")
    return redirect("accounts:users_list")


# ----------------------------
# 6) user_edit_view (Admin)
# ----------------------------
@admin_required_view
def user_edit_view(request, user_id):
    current_user = request.current_user
    user = get_object_or_404(Users, UserID=user_id)

    if request.method == "GET":
        groups = [_norm_group(g) for g in Groups.objects.all().order_by("GroupName")]
        current_group_ids = list(
            UserGroups.objects.filter(UserID=user).values_list("GroupID_id", flat=True)
        )

        return render(request, "accounts/user_form.html", {
            "mode": "edit",
            "user_obj": user,
            "groups": groups,
            "current_group_ids": current_group_ids,
            "is_admin": _is_admin(current_user),
            "is_clerk": _is_clerk(current_user),
        })

    username = (request.POST.get("username") or "").strip()
    email = (request.POST.get("email") or "").strip()
    full_name = (request.POST.get("full_name") or "").strip()
    password = (request.POST.get("password") or "").strip()
    confirm_password = (request.POST.get("confirm_password") or "").strip()

    if not username:
        messages.error(request, "Username is required.")
        return redirect("accounts:user_edit", user_id=user.UserID)

    existing = Users.objects.filter(Username=username).exclude(UserID=user.UserID).first()
    if existing:
        messages.error(request, "Username already exists.")
        return redirect("accounts:user_edit", user_id=user.UserID)

    if password or confirm_password:
        if not password or not confirm_password:
            messages.error(request, "Both new password fields are required to change the password.")
            return redirect("accounts:user_edit", user_id=user.UserID)

        if password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return redirect("accounts:user_edit", user_id=user.UserID)

        user.PasswordHash = make_password(password)

    user.Username = username
    user.Email = email or None

    if hasattr(user, "FullName"):
        user.FullName = full_name

    if hasattr(user, "UpdatedAt"):
        user.UpdatedAt = timezone.now()

    user.save()

    group_id = (request.POST.get("group_id") or "").strip()

    if not group_id:
        messages.error(request, "A role is required.")
        return redirect("accounts:user_edit", user_id=user.UserID)

    try:
        group_id_int = int(group_id)
    except ValueError:
        messages.error(request, "Invalid role selected.")
        return redirect("accounts:user_edit", user_id=user.UserID)

    UserGroups.objects.filter(UserID=user).delete()
    UserGroups.objects.create(UserID=user, GroupID_id=group_id_int)

    # =========================================================
    # FIXED: _audit(request, event_type, details)
    # =========================================================
    _audit(
        request,
        "USER_EDIT",
        f"Updated user UserID={user.UserID} Username={user.Username}",
    )

    messages.success(request, "User updated successfully.")
    return redirect("accounts:user_detail", user_id=user.UserID)

# ----------------------------
# 7) user_disable_view (Admin)
# ----------------------------
@admin_required_view
def user_disable_view(request, user_id):
    user = get_object_or_404(Users, UserID=user_id)

    user.IsActive = not user.IsActive
    user.save()

    state = "enabled" if user.IsActive else "disabled"
    _audit(request, event_type="USER_TOGGLE_ACTIVE", details=f"{state.title()} user {user.Username}.")
    messages.success(request, f"User {user.Username} has been {state}.")
    return redirect("accounts:users_list")

# ----------------------------
# 8) groups_list_view (Admin)
# ----------------------------
@admin_required_view
def groups_list_view(request):
    groups = [_norm_group(g) for g in Groups.objects.all().order_by("GroupName")]
    return render(request, "accounts/groups_list.html", {"groups": groups})


# ----------------------------
# 9) group_permissions_view (Admin)
# ----------------------------
@admin_required_view
def group_permissions_view(request, group_id):
    group = _norm_group(get_object_or_404(Groups, GroupID=group_id))
    permissions = Permissions.objects.all().order_by("PermissionCode")

    if request.method == "POST":
        selected_permission_ids = set()
        for pid in request.POST.getlist("permission_ids"):
            try:
                selected_permission_ids.add(int(pid))
            except Exception:
                pass

        GroupPermissions.objects.filter(GroupID_id=group.GroupID).exclude(
            PermissionID_id__in=selected_permission_ids
        ).delete()

        for pid in selected_permission_ids:
            GroupPermissions.objects.get_or_create(
                GroupID_id=group.GroupID,
                PermissionID_id=pid,
            )

        messages.success(request, f"Permissions updated for group '{group.GroupName}'.")
        return redirect("accounts:groups_list")

    assigned_permission_ids = set(
        GroupPermissions.objects.filter(GroupID_id=group.GroupID).values_list(
            "PermissionID_id", flat=True
        )
    )

    return render(request, "accounts/group_permissions.html", {
        "group": group,
        "permissions": permissions,
        "assigned_permission_ids": assigned_permission_ids,
    })

# Backward-compatible aliases (internal)
User = Users
Group = Groups
Permission = Permissions
UserGroup = UserGroups
GroupPermission = GroupPermissions
