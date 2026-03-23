from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from apps.records.models import ExternalCompanyNames
from apps.organization.models import Departments
from apps.workflow.models import AuditLogs

# Optional (only if you want stats on detail page)
try:
    from apps.records.models import Records
except Exception:
    Records = None


# ----------------------------
# Helpers (same auth approach)
# ----------------------------
def _get_current_user(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    from apps.accounts.models import Users  # local import avoids circular imports
    try:
        return Users.objects.get(UserID=user_id, IsActive=True)
    except Users.DoesNotExist:
        return None


def _is_admin(request):
    """
    Correct relations/fields:
      Groups -> reverse relation is 'usergroups'
      Groups field is GroupName
      UserGroups FK field to Users is UserID
    """
    user = _get_current_user(request)
    if not user:
        return False
    from apps.accounts.models import Groups
    return Groups.objects.filter(
        usergroups__UserID=user,
        GroupName__iexact="Admin"
    ).exists()


def login_required_view(view_func):
    def wrapper(request, *args, **kwargs):
        user = _get_current_user(request)
        if not user:
            return redirect("accounts:login")
        request.current_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required_view(view_func):
    def wrapper(request, *args, **kwargs):
        user = _get_current_user(request)
        if not user:
            return redirect("accounts:login")
        if not _is_admin(request):
            return redirect("accounts:access_denied")
        request.current_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def _audit(request, event_type: str, details: str = ""):
    """
    Schema-aligned AuditLogs:
    EventType, ActorUserID, Details, EventTime
    """
    user = _get_current_user(request)
    try:
        AuditLogs.objects.create(
            EventType=event_type,
            ActorUserID=user,
            Details=details,
            EventTime=timezone.now()
        )
    except Exception:
        pass


# -----------------------------------------
# 1) departments_list_view
# -----------------------------------------
@login_required_view
def departments_list_view(request):
    """
    Departments model has:
      DepartmentID, DepartmentName, Description, CreatedAt
    """
    qs = Departments.objects.all().order_by("DepartmentName")

    return render(request, "organization/departments_list.html", {
        "departments": qs,
        "show_all": True,      # kept to avoid template condition errors
        "is_admin": _is_admin(request),
    })


# -----------------------------------------
# 2) department_create_view (Admin)
# -----------------------------------------
@admin_required_view
def department_create_view(request):
    if request.method == "GET":
        return render(request, "organization/department_form.html", {
            "mode": "create",
        })

    # Read inputs
    name = (request.POST.get("name") or "").strip()
    description = (request.POST.get("description") or "").strip()

    # Validate
    if not name:
        messages.error(request, "Department name is required.")
        return redirect("organization:department_create")

    # Prevent duplicates
    if Departments.objects.filter(DepartmentName__iexact=name).exists():
        messages.error(request, "A department with that name already exists.")
        return redirect("organization:department_create")

    # Create department
    dept = Departments.objects.create(
        DepartmentName=name,
        Description=description or None,
        CreatedAt=timezone.now()
    )

    _audit(request, event_type="DEPARTMENT_CREATE", details=f"Created department: {name}")
    messages.success(request, "Department created successfully.")

    # Redirect to detail page
    return redirect("organization:department_detail", department_id=dept.DepartmentID)


# -----------------------------------------
# 3) department_edit_view (Admin)
# -----------------------------------------
@admin_required_view
def department_edit_view(request, department_id):
    # PK is DepartmentID
    dept = get_object_or_404(Departments, DepartmentID=department_id)

    if request.method == "GET":
        return render(request, "organization/department_form.html", {
            "mode": "edit",
            "department": dept,
        })

    name = (request.POST.get("name") or "").strip()
    description = (request.POST.get("description") or "").strip()

    if not name:
        messages.error(request, "Department name is required.")
        return redirect("organization:department_edit", department_id=dept.DepartmentID)

    # Duplicate name check (exclude current)
    if Departments.objects.filter(DepartmentName__iexact=name).exclude(DepartmentID=dept.DepartmentID).exists():
        messages.error(request, "Another department already uses that name.")
        return redirect("organization:department_edit", department_id=dept.DepartmentID)

    # ✅ FIX: save BOTH name and description
    dept.DepartmentName = name
    dept.Description = description or None  # <-- this was missing in your file
    dept.save()

    _audit(request, event_type="DEPARTMENT_EDIT", details=f"Edited department: {name}")
    messages.success(request, "Department updated successfully.")
    return redirect("organization:department_detail", department_id=dept.DepartmentID)


# -----------------------------------------
# 4) department_disable_view (Admin)
# -----------------------------------------
@admin_required_view
def department_disable_view(request, department_id):
    """
    Your Departments model has no IsActive column.
    Keep endpoint so templates/urls don't break.
    """
    messages.error(request, "Departments cannot be disabled because there is no IsActive field in the Departments table.")
    return redirect("organization:departments_list")


# -----------------------------------------
# 5) department_detail_view (Optional stats)
# -----------------------------------------
@login_required_view
def department_detail_view(request, department_id):
    dept = get_object_or_404(Departments, DepartmentID=department_id)

    stats = {}
    if Records is not None:
        # NOTE: Implementing stats correctly depends on your Records FK field naming.
        # Keeping this safe/empty until you confirm the exact FK field.
        stats = {}

    return render(request, "organization/department_detail.html", {
        "department": dept,
        "stats": stats,
        "is_admin": _is_admin(request),
    })
    

@login_required_view
def external_companies_list_view(request):
    qs = ExternalCompanyNames.objects.all().order_by("CompanyName")

    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(CompanyName__icontains=q) |
            Q(Description__icontains=q)
        )

    return render(request, "organization/external_companies_list.html", {
        "external_companies": qs,
        "q": q,
        "show_all": True,
        "is_admin": _is_admin(request),
    })


@login_required_view
def external_company_detail_view(request, company_id):
    company = get_object_or_404(
        ExternalCompanyNames,
        ExternalCompanyNameID=company_id
    )

    return render(request, "organization/external_company_detail.html", {
        "company": company,
        "is_admin": _is_admin(request),
    })


@admin_required_view
def external_company_edit_view(request, company_id):
    company = get_object_or_404(
        ExternalCompanyNames,
        ExternalCompanyNameID=company_id
    )

    if request.method == "GET":
        return render(request, "organization/external_company_form.html", {
            "mode": "edit",
            "company": company,
            "is_admin": _is_admin(request),
        })

    company_name = (request.POST.get("company_name") or "").strip()
    description = (request.POST.get("description") or "").strip()

    if not company_name:
        messages.error(request, "Company name is required.")
        return redirect("organization:external_company_edit", company_id=company.ExternalCompanyNameID)

    duplicate = ExternalCompanyNames.objects.filter(
        CompanyName__iexact=company_name
    ).exclude(
        ExternalCompanyNameID=company.ExternalCompanyNameID
    ).exists()

    if duplicate:
        messages.error(request, "Another external company already uses that name.")
        return redirect("organization:external_company_edit", company_id=company.ExternalCompanyNameID)

    company.CompanyName = company_name
    company.Description = description or None
    company.UpdatedAt = timezone.now()
    company.save()

    _audit(
        request,
        event_type="EXTERNAL_COMPANY_EDIT",
        details=f"Edited external company: {company.CompanyName}"
    )
    messages.success(request, "External company updated successfully.")
    return redirect("organization:external_company_detail", company_id=company.ExternalCompanyNameID)