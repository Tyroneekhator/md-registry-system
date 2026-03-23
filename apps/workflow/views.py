from functools import wraps

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.http import HttpResponseForbidden
from django.db.models import Q
from apps.accounts.models import Users

from apps.records.models import Records, RecordAttachments
from apps.workflow.models import ActionRequests, AuditLogs


# ============================================================
# Auth helpers (session-based)
# ============================================================
def _get_current_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    from apps.accounts.models import Users

    try:
        return Users.objects.get(UserID=user_id, IsActive=True)
    except Users.DoesNotExist:
        return None


def _user_in_group(user, group_name: str) -> bool:
    if not user:
        return False

    from apps.accounts.models import UserGroups

    return UserGroups.objects.filter(
        UserID=user,
        GroupID__GroupName__iexact=group_name
    ).exists()


def _is_admin(user) -> bool:
    return _user_in_group(user, "Admin")


def _is_clerk(user) -> bool:
    return _user_in_group(user, "Clerk")


def login_required_view(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = _get_current_user(request)
        if not user:
            return redirect("accounts:login")
        request.current_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required_view(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = _get_current_user(request)
        if not user:
            return redirect("accounts:login")
        if not _is_admin(user):
            return redirect("accounts:access_denied")
        request.current_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def clerk_required_view(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = _get_current_user(request)
        if not user:
            return redirect("accounts:login")
        if not _is_clerk(user):
            return redirect("accounts:access_denied")
        request.current_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_or_clerk_required_view(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = _get_current_user(request)
        if not user:
            return redirect("accounts:login")

        request.current_user = user

        if _is_admin(user) or _is_clerk(user):
            return view_func(request, *args, **kwargs)

        return redirect("accounts:access_denied")
    return wrapper


def _audit(request, event_type: str, details: str = "", target_record=None, target_request=None):
    user = _get_current_user(request)
    if user is None:
        return

    data = {
        "EventType": event_type,
        "ActorUserID": user,
        "Details": details,
        "EventTime": timezone.now(),
    }

    if target_record is not None:
        data["TargetRecordID"] = target_record
    if target_request is not None:
        data["TargetRequestID"] = target_request

    AuditLogs.objects.create(**data)


# ============================================================
# Soft-delete + restore helpers
# ============================================================
def _mark_record_deleted(rec, user=None):
    now = timezone.now()

    if hasattr(rec, "IsDeleted"):
        rec.IsDeleted = True

    if hasattr(rec, "deleted_at"):
        rec.deleted_at = now
    if hasattr(rec, "is_deleted"):
        rec.is_deleted = True
    if hasattr(rec, "is_active"):
        rec.is_active = False

    rec.save()


def _restore_record(rec, user=None):
    if hasattr(rec, "IsDeleted"):
        rec.IsDeleted = False

    if hasattr(rec, "deleted_at"):
        rec.deleted_at = None
    if hasattr(rec, "is_deleted"):
        rec.is_deleted = False
    if hasattr(rec, "is_active"):
        rec.is_active = True

    rec.save()



# ============================================================
# CORRECTION: helper for clerk permanent-delete request checks
# ============================================================
def _get_pending_permanent_delete_request_for_record(record):
    return ActionRequests.objects.filter(
        TargetRecordID=record,
        RequestType__iexact="PERMANENT_DELETE",
        Status__iexact="pending",
    ).order_by("-RequestID").first()
    



# ============================================================
# CORRECTION: helper to detect deleted records safely
# ============================================================
def _is_record_deleted(rec):
    if hasattr(rec, "IsDeleted"):
        return bool(rec.IsDeleted)
    if hasattr(rec, "is_deleted"):
        return bool(rec.is_deleted)
    if hasattr(rec, "deleted_at"):
        return rec.deleted_at is not None
    return False


# ============================================================
# CORRECTION: helper for permanent delete operation
# removes attachments first, then deletes record
# ============================================================
def _permanently_delete_record(rec):
    RecordAttachments.objects.filter(RecordID_id=rec.RecordID).delete()
    rec.delete()
    


# ============================================================
# Parse edit request lines for request detail viewer
# Expected:
# CHANGE|FieldName|old value|new value
# ============================================================
def _parse_request_changes(request_details: str):
    changes = []

    if not request_details:
        return changes

    for line in request_details.splitlines():
        line = (line or "").strip()
        if not line.startswith("CHANGE|"):
            continue

        parts = line.split("|", 3)
        if len(parts) != 4:
            continue

        _, field_name, old_value, new_value = parts

        old_display = old_value if old_value != "" else "—"
        new_display = new_value if new_value != "" else "—"

        changes.append({
            "field": field_name,
            "old": old_display,
            "new": new_display,
            "changed": str(old_display).strip() != str(new_display).strip(),
        })

    return changes


def _parse_change_datetime(value):
    value = (value or "").strip()
    if not value or value == "—":
        return None

    dt = parse_datetime(value)
    if dt:
        return dt

    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            from datetime import datetime
            return datetime.strptime(value, fmt)
        except Exception:
            pass

    return None


def _get_related_model(instance, field_name):
    try:
        return instance._meta.get_field(field_name).remote_field.model
    except Exception:
        return None


def _find_department_by_name(rec, field_name, dept_name):
    dept_name = (dept_name or "").strip()
    if not dept_name:
        return None

    model = _get_related_model(rec, field_name)
    if model is None:
        return None

    for attr in ("DepartmentName", "department_name", "name", "Name"):
        try:
            return model.objects.filter(**{f"{attr}__iexact": dept_name}).first()
        except Exception:
            continue

    return None


# ============================================================
# CORRECTION: helper for clerk restore-request duplication checks
# ============================================================
def _get_pending_restore_request_for_record(record):
    return ActionRequests.objects.filter(
        TargetRecordID=record,
        RequestType__iexact="RESTORE",
        Status__iexact="pending",
    ).order_by("-RequestID").first()


# ============================================================
# 1) requests_list_view (STRICT ROLE-BASED SCOPE)
# ============================================================
@login_required_view
def requests_list_view(request):
    user = request.current_user
    
    if not (_is_admin(user) or _is_clerk(user)):
        messages.error(request, "You do not have permission to access Requests.")
        return redirect("records:dashboard")

    status = request.GET.get("status", "")
    q = (request.GET.get("q") or "").strip()
    
    # =========================================================
    # NEW: admin-only clerk filter
    # =========================================================
    clerk_id = (request.GET.get("clerk_id") or "").strip()
    

    # =========================================================
    # 🔒 FORCE SCOPE BY ROLE (IGNORE URL PARAM)
    # =========================================================
    if _is_admin(user):
        scope = "all"
        qs = ActionRequests.objects.all()

        if clerk_id:
            qs = qs.filter(RequestedByUserID_id=clerk_id)
            
        clerks = Users.objects.filter(
            usergroups__GroupID__GroupName__iexact="Clerk",
            IsActive=True,
        ).distinct().order_by("Username")
        
    elif _is_clerk(user):
        scope = "mine"
        qs = ActionRequests.objects.filter(RequestedByUserID=user)
        clerks = []
        
        clerk_id = ""

    else:
        scope=""
        qs = ActionRequests.objects.none()
        clerks = []
        clerk_id = ""

    # =========================================================
    # ORDERING
    # =========================================================
    qs = qs.order_by("-RequestID")

    # =========================================================
    # STATUS FILTER
    # =========================================================
    if status:
        qs = qs.filter(Status__iexact=status)

    # =========================================================
    # SEARCH
    # =========================================================
    if q:
        filters = (
            Q(RequestType__icontains=q) |
            Q(RequestDetails__icontains=q) |
            Q(Status__icontains=q)
        )
        try:
            filters |= Q(RequestedByUserID__Username__icontains=q)
        except Exception:
            pass

        qs = qs.filter(filters)

    return render(request, "workflow/requests_list.html", {
        "requests": qs,
        "scope": scope,
        "status": status,
        "q": q,
        "clerks":clerks,
        "clerk_id":clerk_id,
        "is_admin": _is_admin(user),
        "is_clerk": _is_clerk(user),
    })


# ============================================================
# 2) request_create_view
# ============================================================
@clerk_required_view
def request_create_view(request):
    user = request.current_user

    if request.method == "GET":
        records = Records.objects.all().order_by("-RecordID")[:500]
        return render(request, "workflow/request_form.html", {
            "mode": "create",
            "records": records,
        })

    record_id = request.POST.get("record_id")
    request_type = (request.POST.get("request_type") or "").strip()
    details = (request.POST.get("details") or "").strip()

    if not record_id or not request_type:
        messages.error(request, "Record and request type are required.")
        return redirect("workflow:request_create")

    rec = get_object_or_404(Records, RecordID=record_id)

    req = ActionRequests.objects.create(
        RequestType=request_type.upper(),
        TargetRecordID=rec,
        RequestedByUserID=user,
        RequestDetails=details,
        Status="pending",
        CreatedAt=timezone.now(),
    )

    _audit(
        request,
        "REQUEST_CREATE",
        f"Created request RequestID={req.RequestID} for RecordID={rec.RecordID} type={request_type.upper()}",
        target_record=rec,
        target_request=req,
    )

    messages.success(request, "Request submitted successfully.")
    return redirect("workflow:requests_list")

# ============================================================
# 3) request_detail_view
# ============================================================
@login_required_view
def request_detail_view(request, request_id):
    user = request.current_user
    req = get_object_or_404(ActionRequests, RequestID=request_id)
    rec = req.TargetRecordID

    if not _is_admin(user) and req.RequestedByUserID_id != user.UserID:
        return redirect("accounts:access_denied")

    changes = _parse_request_changes(req.RequestDetails or "")

    return render(request, "workflow/request_detail.html", {
        "req": req,
        "record": rec,
        "changes": changes,
        "is_admin": _is_admin(user),
        "is_clerk": _is_clerk(user),
    })


# ============================================================
# 4) request_approve_view
# ============================================================
@admin_required_view
def request_approve_view(request, request_id):
    user = request.current_user
    req = get_object_or_404(ActionRequests, RequestID=request_id)

    if str(req.Status or "").lower() != "pending":
        messages.info(request, "This request is not pending.")
        return redirect("workflow:request_detail", request_id=req.RequestID)

    rec = req.TargetRecordID
    action = (req.RequestType or "").upper()

    if action == "DELETE":
        _mark_record_deleted(rec, user=user)
        _audit(
            request,
            "REQUEST_APPROVE_DELETE",
            f"Approved DELETE RequestID={req.RequestID} -> RecordID={rec.RecordID} soft-deleted",
            target_record=rec,
            target_request=req,
        )

    elif action == "RESTORE":
        _restore_record(rec, user=user)
        _audit(
            request,
            "REQUEST_APPROVE_RESTORE",
            f"Approved RESTORE RequestID={req.RequestID} -> RecordID={rec.RecordID} restored",
            target_record=rec,
            target_request=req,
        )
        
    elif action == "PERMANENT_DELETE":
        if rec and _is_record_deleted(rec):
            rec_id = rec.RecordID
            _permanently_delete_record(rec)
            
            req.TargetRecordID = None

            _audit(
                request,
                "REQUEST_APPROVE_PERMANENT_DELETE",
                f"Approved PERMANENT_DELETE RequestID={req.RequestID} -> RecordID={rec_id} permanently deleted",
                target_request=req,
            )
        else:
            _audit(
                request,
                "REQUEST_APPROVE_PERMANENT_DELETE_SKIPPED",
                f"Approved RequestID={req.RequestID} but target record was missing or not deleted.",
                target_request=req,
            )

    elif action == "EDIT":
        changes = _parse_request_changes(req.RequestDetails or "")

        for item in changes:
            field = item["field"]
            new_value = item["new"]

            if field == "MessengerName":
                rec.MessengerName = None if new_value == "—" else new_value

            elif field == "Subject":
                rec.Subject = None if new_value == "—" else new_value

            elif field == "Description":
                rec.Description = None if new_value == "—" else new_value

            elif field == "InvoiceNumber":
                try:
                    cleaned = str(new_value).replace(",", "").strip()
                    rec.InvoiceNumber = int(cleaned) if cleaned and cleaned != "—" else None
                except Exception:
                    pass

            elif field == "DateReceived":
                rec.DateReceived = _parse_change_datetime(new_value)

            elif field == "IncomingDepartment":
                dept = _find_department_by_name(rec, "IncomingDepartmentID", new_value)
                rec.IncomingDepartmentID = dept

            elif field == "OutgoingDepartment":
                dept = _find_department_by_name(rec, "OutgoingDepartmentID", new_value)
                rec.OutgoingDepartmentID = dept

            elif field == "DateDispatched":
                rec.DateDispatched = _parse_change_datetime(new_value)

            elif field == "Returned":
                cleaned = None if new_value in ("", "—") else new_value
                if cleaned in ("Yes", "No", None):
                    rec.Returned = cleaned

            elif field == "DateReturned":
                cleaned = (new_value or "").strip()
                rec.DateReturned = None if cleaned in ("", "—") else parse_date(cleaned)

            elif field == "Status":
                rec.Status = None if new_value == "—" else new_value

        if hasattr(rec, "UpdatedAt"):
            rec.UpdatedAt = timezone.now()

        rec.save()

        _audit(
            request,
            "REQUEST_APPROVE_EDIT",
            f"Approved EDIT RequestID={req.RequestID} -> RecordID={rec.RecordID} updated",
            target_record=rec,
            target_request=req,
        )

    else:
        _audit(
            request,
            "REQUEST_APPROVE_OTHER",
            f"Approved RequestID={req.RequestID} type={action} (no auto-apply implemented)",
            target_record=rec,
            target_request=req,
        )

    req.Status = "approved"
    req.ReviewedByUserID = user
    req.ReviewedAt = timezone.now()
    
    if action == "PERMANENT_DELETE":
        req.TargetRecordID = None
    
    req.save()
    
    

    messages.success(request, "Request approved.")
    return redirect("workflow:request_detail", request_id=req.RequestID)


# ============================================================
# 5) request_reject_view
# ============================================================
@admin_required_view
def request_reject_view(request, request_id):
    user = request.current_user
    req = get_object_or_404(ActionRequests, RequestID=request_id)

    if request.method == "GET":
        return render(request, "workflow/request_reject.html", {"req": req})

    reason = (request.POST.get("reason") or "").strip()
    if not reason:
        messages.error(request, "Rejection reason is required.")
        return redirect("workflow:request_reject", request_id=req.RequestID)

    req.Status = "rejected"
    req.ReviewedByUserID = user
    req.ReviewedAt = timezone.now()

    if req.RequestDetails:
        req.RequestDetails = f"{req.RequestDetails}\n\n[REJECTION REASON]: {reason}"
    else:
        req.RequestDetails = f"[REJECTION REASON]: {reason}"

    req.save()

    _audit(
        request,
        "REQUEST_REJECT",
        f"Rejected RequestID={req.RequestID}. Reason: {reason[:200]}",
        target_record=req.TargetRecordID,
        target_request=req,
    )

    messages.success(request, "Request rejected.")
    return redirect("workflow:request_detail", request_id=req.RequestID)


# ============================================================
# 6) deleted_records_list_view
# ============================================================
@admin_or_clerk_required_view
def deleted_records_list_view(request):
    user = request.current_user
    q = (request.GET.get("q") or "").strip()
    request_state = (request.GET.get("request_state") or "").strip()

    qs = Records.objects.all()

    if hasattr(Records, "IsDeleted"):
        qs = qs.filter(IsDeleted=True)
    elif hasattr(Records, "is_deleted"):
        qs = qs.filter(is_deleted=True)
    elif hasattr(Records, "deleted_at"):
        qs = qs.filter(deleted_at__isnull=False)
    else:
        qs = qs.none()

    if q:
        filters = Q()
        for field in ["InvoiceNumber", "MessengerName", "Subject", "Description"]:
            if hasattr(Records, field):
                filters |= Q(**{f"{field}__icontains": q})
        qs = qs.filter(filters)

    qs = qs.order_by("-RecordID")

    
    if request_state == "restore_requested":
        restore_ids = ActionRequests.objects.filter(
            RequestType__iexact="RESTORE",
            Status__iexact="pending",
            TargetRecordID__isnull=False,
        ).values_list("TargetRecordID__RecordID", flat=True)

        qs = qs.filter(RecordID__in=restore_ids)
    elif request_state == "permanent_delete_requested":
        permanent_delete_ids = ActionRequests.objects.filter(
            RequestType__iexact="PERMANENT_DELETE",
            Status__iexact="pending",
            TargetRecordID__isnull=False,
        ).values_list("TargetRecordID__RecordID", flat=True)

        qs = qs.filter(RecordID__in=permanent_delete_ids)
        
    qs = qs.order_by("-RecordID")
    
    for rec in qs:
        rec.pending_restore_request = _get_pending_restore_request_for_record(rec)
        rec.pending_permanent_delete_request = _get_pending_permanent_delete_request_for_record(rec)


    return render(request, "workflow/deleted_records_list.html", {
        "records": qs,
        "q": q,
        "request_state": request_state,
        "is_admin": _is_admin(user),   # CORRECTION
        "is_clerk": _is_clerk(user),   # CORRECTION
    })


# ============================================================
# 7) CORRECTION: clerk restore-request action
# ============================================================
@clerk_required_view
def record_restore_request_view(request, record_id):
    user = request.current_user

    if request.method != "POST":
        return redirect("workflow:deleted_records_list")

    rec = get_object_or_404(Records, RecordID=record_id)

    is_deleted = False
    if hasattr(rec, "IsDeleted"):
        is_deleted = bool(rec.IsDeleted)
    elif hasattr(rec, "is_deleted"):
        is_deleted = bool(rec.is_deleted)
    elif hasattr(rec, "deleted_at"):
        is_deleted = rec.deleted_at is not None

    if not is_deleted:
        messages.error(request, "This record is not in the deleted records list.")
        return redirect("workflow:deleted_records_list")

    existing = _get_pending_restore_request_for_record(rec)
    if existing:
        messages.info(request, "A restore request is already pending for this record.")
        return redirect("workflow:request_detail", request_id=existing.RequestID)

    req = ActionRequests.objects.create(
        RequestType="RESTORE",
        TargetRecordID=rec,
        RequestedByUserID=user,
        RequestDetails=f"Clerk requested restore for deleted record RecordID={rec.RecordID}.",
        Status="pending",
        CreatedAt=timezone.now(),
    )

    _audit(
        request,
        "REQUEST_CREATE_RESTORE",
        f"Clerk requested restore for RecordID={rec.RecordID} (RequestID={req.RequestID})",
        target_record=rec,
        target_request=req,
    )

    messages.success(request, "Restore request submitted for admin approval.")
    return redirect("workflow:deleted_records_list")


# ============================================================
# 8) record_restore_view
# ============================================================
@admin_required_view
def record_restore_view(request, record_id):
    user = request.current_user
    rec = get_object_or_404(Records, RecordID=record_id)

    _restore_record(rec, user=user)
    _audit(
        request,
        "RECORD_RESTORE",
        f"Restored RecordID={rec.RecordID}",
        target_record=rec
    )

    messages.success(request, "Record restored successfully.")
    return redirect("workflow:deleted_records_list")


# ============================================================
# CORRECTION: bulk restore deleted records
# Admin  -> immediate restore
# Clerk  -> create one RESTORE request per selected record
# ============================================================
@admin_or_clerk_required_view
def bulk_restore_deleted_records_view(request):
    user = request.current_user

    if request.method != "POST":
        return redirect("workflow:deleted_records_list")

    raw_ids = request.POST.getlist("record_ids")
    record_ids = [int(x) for x in raw_ids if str(x).strip().isdigit()]
    record_ids = list(dict.fromkeys(record_ids))

    if not record_ids:
        messages.error(request, "Please select at least one deleted record.")
        return redirect("workflow:deleted_records_list")

    records = Records.objects.filter(RecordID__in=record_ids)

    restored_count = 0
    request_count = 0
    skipped_pending_count = 0

    for rec in records:
        if not _is_record_deleted(rec):
            continue

        if _is_admin(user):
            _restore_record(rec, user=user)
            _audit(
                request,
                "RECORD_RESTORE_BULK_ITEM",
                f"Bulk restored RecordID={rec.RecordID}",
                target_record=rec,
            )
            restored_count += 1
        else:
            existing = _get_pending_restore_request_for_record(rec)
            if existing:
                skipped_pending_count += 1
                continue

            req = ActionRequests.objects.create(
                RequestType="RESTORE",
                TargetRecordID=rec,
                RequestedByUserID=user,
                RequestDetails=f"Bulk restore request for deleted record RecordID={rec.RecordID}.",
                Status="pending",
                CreatedAt=timezone.now(),
            )

            _audit(
                request,
                "REQUEST_CREATE_RESTORE_BULK_ITEM",
                f"Clerk requested bulk restore for RecordID={rec.RecordID} (RequestID={req.RequestID})",
                target_record=rec,
                target_request=req,
            )
            request_count += 1

    if _is_admin(user):
        messages.success(request, f"{restored_count} deleted record(s) restored.")
        return redirect("workflow:deleted_records_list")

    if request_count > 0:
        messages.success(request, f"{request_count} restore request(s) submitted for admin approval.")
    elif skipped_pending_count > 0:
        messages.info(request, "No new restore requests were created because selected records already had pending restore requests.")
    else:
        messages.info(request, "No restore requests were created.")

    return redirect("workflow:requests_list")


# ============================================================
# CORRECTION: bulk permanent delete deleted records
# Admin  -> immediate permanent delete
# Clerk  -> create one PERMANENT_DELETE request per record
# ============================================================
@admin_or_clerk_required_view
def bulk_permanent_delete_records_view(request):
    user = request.current_user

    if request.method != "POST":
        return redirect("workflow:deleted_records_list")

    raw_ids = request.POST.getlist("record_ids")
    record_ids = [int(x) for x in raw_ids if str(x).strip().isdigit()]
    record_ids = list(dict.fromkeys(record_ids))

    if not record_ids:
        messages.error(request, "Please select at least one deleted record.")
        return redirect("workflow:deleted_records_list")

    records = Records.objects.filter(RecordID__in=record_ids)

    deleted_count = 0
    request_count = 0
    skipped_pending_count = 0

    for rec in records:
        if not _is_record_deleted(rec):
            continue

        if _is_admin(user):
            rec_id = rec.RecordID
            _permanently_delete_record(rec)

            AuditLogs.objects.create(
                EventType="RECORD_PERMANENT_DELETE_BULK_ITEM",
                ActorUserID=user,
                TargetRecordID=None,
                EventTime=timezone.now(),
                Details=f"Bulk permanently deleted RecordID={rec_id}",
            )
            deleted_count += 1
        else:
            existing = _get_pending_permanent_delete_request_for_record(rec)
            if existing:
                skipped_pending_count += 1
                continue

            req = ActionRequests.objects.create(
                RequestType="PERMANENT_DELETE",
                TargetRecordID=rec,
                RequestedByUserID=user,
                RequestDetails=f"Bulk permanent delete request for deleted record RecordID={rec.RecordID}.",
                Status="pending",
                CreatedAt=timezone.now(),
            )

            _audit(
                request,
                "REQUEST_CREATE_PERMANENT_DELETE_BULK_ITEM",
                f"Clerk requested bulk permanent delete for RecordID={rec.RecordID} (RequestID={req.RequestID})",
                target_record=rec,
                target_request=req,
            )
            request_count += 1

    if _is_admin(user):
        messages.success(request, f"{deleted_count} deleted record(s) permanently removed.")
        return redirect("workflow:deleted_records_list")

    if request_count > 0:
        messages.success(request, f"{request_count} permanent delete request(s) submitted for admin approval.")
    elif skipped_pending_count > 0:
        messages.info(request, "No new permanent delete requests were created because selected records already had pending permanent delete requests.")
    else:
        messages.info(request, "No permanent delete requests were created.")

    return redirect("workflow:requests_list")


# ============================================================
# 9) audit_dashboard_view
# ============================================================
@admin_required_view
def audit_dashboard_view(request):
    event_type = (request.GET.get("event_type") or "").strip()
    user_q = (request.GET.get("user") or "").strip()
    date_from = (request.GET.get("date_from") or "").strip()
    date_to = (request.GET.get("date_to") or "").strip()

    qs = AuditLogs.objects.all()

    if hasattr(AuditLogs, "IsDeleted"):
        qs = qs.filter(IsDeleted=False)

    if hasattr(AuditLogs, "IsDeleted"):
        action_choices = (
            AuditLogs.objects.filter(IsDeleted=False)
            .values_list("EventType", flat=True)
            .distinct()
            .order_by("EventType")
        )
    else:
        action_choices = (
            AuditLogs.objects
            .values_list("EventType", flat=True)
            .distinct()
            .order_by("EventType")
        )

    if event_type:
        qs = qs.filter(EventType__iexact=event_type)

    if user_q:
        qs = qs.filter(ActorUserID__Username__icontains=user_q)

    df = parse_date(date_from) if date_from else None
    dt = parse_date(date_to) if date_to else None
    if df:
        qs = qs.filter(EventTime__date__gte=df)
    if dt:
        qs = qs.filter(EventTime__date__lte=dt)

    total_logs = qs.count()
    total_logins = qs.filter(EventType__icontains="login").count()
    total_changes = qs.filter(EventType__iexact="RECORD_EDIT").count()
    recent = qs.order_by("-EventTime")[:20]

    return render(request, "workflow/audit_dashboard.html", {
        "recent_logs": recent,
        "event_type": event_type,
        "user_q": user_q,
        "date_from": date_from,
        "date_to": date_to,
        "action_choices": action_choices,
        "total_logs": total_logs,
        "total_logins": total_logins,
        "total_changes": total_changes,
    })


# ============================================================
# 10) audit_logs_list_view
# ============================================================
@admin_required_view
def audit_logs_list_view(request):
    q = (request.GET.get("q") or "").strip()
    event_type = (request.GET.get("event_type") or "").strip()
    date_from = (request.GET.get("date_from") or "").strip()
    date_to = (request.GET.get("date_to") or "").strip()

    qs = AuditLogs.objects.all()

    if hasattr(AuditLogs, "IsDeleted"):
        qs = qs.filter(IsDeleted=False)
        action_choices = (
            AuditLogs.objects.filter(IsDeleted=False)
            .values_list("EventType", flat=True)
            .distinct()
            .order_by("EventType")
        )
    else:
        action_choices = (
            AuditLogs.objects
            .values_list("EventType", flat=True)
            .distinct()
            .order_by("EventType")
        )

    if event_type:
        qs = qs.filter(EventType__iexact=event_type)

    if q:
        filters = (
            Q(Details__icontains=q) |
            Q(EventType__icontains=q) |
            Q(ActorUserID__Username__icontains=q)
        )
        qs = qs.filter(filters)

    df = parse_date(date_from) if date_from else None
    dt = parse_date(date_to) if date_to else None
    if df:
        qs = qs.filter(EventTime__date__gte=df)
    if dt:
        qs = qs.filter(EventTime__date__lte=dt)

    qs = qs.order_by("-EventTime")

    return render(request, "workflow/audit_logs_list.html", {
        "logs": qs,
        "q": q,
        "event_type": event_type,
        "date_from": date_from,
        "date_to": date_to,
        "action_choices": action_choices,
    })


# ============================================================
# 11) audit_log_detail_view
# ============================================================
@admin_required_view
def audit_log_detail_view(request, log_id):
    log = get_object_or_404(AuditLogs, AuditLogID=log_id)
    return render(request, "workflow/audit_log_detail.html", {"log": log})


# ============================================================
# 12) record_permanent_delete_view
# ============================================================
@admin_required_view
def record_permanent_delete_view(request, record_id):
    user = request.current_user

    if request.method != "POST":
        return redirect("workflow:deleted_records_list")

    rec = get_object_or_404(Records, RecordID=record_id)

    if not getattr(rec, "IsDeleted", False):
        messages.error(request, "This record is not deleted. Soft-delete it first.")
        return redirect("workflow:deleted_records_list")
    
    # CORRECTION: shared helper for permanent delete
    _permanently_delete_record(rec)

    #RecordAttachments.objects.filter(RecordID_id=rec.RecordID).delete()

    #rec.delete()

    AuditLogs.objects.create(
        EventType="RECORD_PERMANENT_DELETE",
        ActorUserID=user,
        TargetRecordID=None,
        EventTime=timezone.now(),
        Details=f"Permanently deleted RecordID={record_id}",
    )

    messages.success(request, "Record permanently deleted.")
    return redirect("workflow:deleted_records_list")



# ============================================================
# CORRECTION: clerk permanent-delete request action
# ============================================================
@clerk_required_view
def record_permanent_delete_request_view(request, record_id):
    user = request.current_user

    if request.method != "POST":
        return redirect("workflow:deleted_records_list")

    rec = get_object_or_404(Records, RecordID=record_id)

    if not _is_record_deleted(rec):
        messages.error(request, "This record is not in the deleted records list.")
        return redirect("workflow:deleted_records_list")

    existing = _get_pending_permanent_delete_request_for_record(rec)
    if existing:
        messages.info(request, "A permanent delete request is already pending for this record.")
        return redirect("workflow:request_detail", request_id=existing.RequestID)

    req = ActionRequests.objects.create(
        RequestType="PERMANENT_DELETE",
        TargetRecordID=rec,
        RequestedByUserID=user,
        RequestDetails=f"Clerk requested permanent delete for deleted record RecordID={rec.RecordID}.",
        Status="pending",
        CreatedAt=timezone.now(),
    )

    _audit(
        request,
        "REQUEST_CREATE_PERMANENT_DELETE",
        f"Clerk requested permanent delete for RecordID={rec.RecordID} (RequestID={req.RequestID})",
        target_record=rec,
        target_request=req,
    )

    messages.success(request, "Permanent delete request submitted for admin approval.")
    return redirect("workflow:deleted_records_list")