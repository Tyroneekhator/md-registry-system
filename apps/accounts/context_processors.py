from typing import Dict
from apps.accounts.models import Users, Groups


def role_flags(request) -> Dict[str, object]:
    """
    Global role flags for ALL templates.
    Uses session user_id (set at login) and checks Groups membership in DB.
    """

    user_id = request.session.get("user_id")
    if not user_id:
        return {
            "is_admin": False,
            "is_clerk": False,
            "is_viewer": False,
            "current_role": "",
        }

    try:
        # ✅ Your Users PK is UserID (not id)
        user = Users.objects.get(UserID=user_id)
    except Users.DoesNotExist:
        return {
            "is_admin": False,
            "is_clerk": False,
            "is_viewer": False,
            "current_role": "",
        }

    # Groups through UserGroups relation (your related_name is "usergroups")
    qs = Groups.objects.filter(usergroups__UserID=user).distinct()

    is_admin = qs.filter(GroupName__iexact="Admin").exists()
    is_clerk = qs.filter(GroupName__iexact="Clerk").exists()
    is_viewer = qs.filter(GroupName__iexact="Viewer").exists()

    # Pick a display role (priority order)
    current_role = "Admin" if is_admin else ("Clerk" if is_clerk else ("Viewer" if is_viewer else ""))

    return {
        "is_admin": is_admin,
        "is_clerk": is_clerk,
        "is_viewer": is_viewer,
        "current_role": current_role,
    }