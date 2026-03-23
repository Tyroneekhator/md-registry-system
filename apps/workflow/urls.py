from django.urls import path
from . import views

app_name = "workflow"

urlpatterns = [
    path("requests/", views.requests_list_view, name="requests_list"),
    path("requests/create/", views.request_create_view, name="request_create"),
    path("requests/<int:request_id>/", views.request_detail_view, name="request_detail"),
    path("requests/<int:request_id>/approve/", views.request_approve_view, name="request_approve"),
    path("requests/<int:request_id>/reject/", views.request_reject_view, name="request_reject"),
    path("deleted-records/", views.deleted_records_list_view, name="deleted_records_list"),
    path("deleted-records/<int:record_id>/restore/", views.record_restore_view, name="record_restore"),
    path(
        "deleted-records/<int:record_id>/request-restore/",
        views.record_restore_request_view,
        name="record_restore_request",
    ),
    path(
        "deleted-records/<int:record_id>/permanent-delete/",
        views.record_permanent_delete_view,
        name="record_permanent_delete",
    ),
    path("deleted-records/bulk-restore/", views.bulk_restore_deleted_records_view, name="bulk_restore_deleted_records"),
    path("deleted-records/bulk-permanent-delete/", views.bulk_permanent_delete_records_view, name="bulk_permanent_delete_records"),
    path("audit/", views.audit_dashboard_view, name="audit_dashboard"),
    path("audit/logs/", views.audit_logs_list_view, name="audit_logs_list"),
    path("audit/logs/<int:log_id>/", views.audit_log_detail_view, name="audit_log_detail"),
    # CORRECTION: clerk permanent-delete request route
    path("deleted-records/<int:record_id>/request-permanent-delete/",views.record_permanent_delete_request_view,name="record_permanent_delete_request"),
]