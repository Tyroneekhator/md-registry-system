from apps.workflow.models import ActionRequests
from apps.accounts.models import Users, UserGroups

def _get_current_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    try:
        return Users.objects.get(UserID=user_id, IsActive=True)
    except Users.DoesNotExist:
        return None

def _user_in_group(user, group_name: str) -> bool:
    if not user:
        return False
    return UserGroups.objects.filter(
        UserID=user,
        GroupID__GroupName__iexact=group_name
    ).exists()

def workflow_pending_counts(request):
    user = _get_current_user(request)

    pending_requests_count = 0

    if user and _user_in_group(user, "Admin"):
        pending_requests_count = ActionRequests.objects.filter(
            Status__iexact="pending"
        ).count()

    return {
        "pending_requests_count": pending_requests_count,
    }