from django.urls import path
from . import views



app_name = "records"

urlpatterns = [
    # Main pages
    path("", views.home_view, name="home"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("table/", views.records_table_view, name="records_table"),

    # IMPORT: your templates are calling {% url 'records_import' %}
    # But your views.py DOES NOT have records_import_view.
    # We map it to the existing excel import view so reverse() works.
    path("import/", views.records_import_excel_view, name="records_import"),

    # Record CRUD
    path("create/", views.record_create_view, name="record_create"),
    path("<int:record_id>/", views.record_detail_view, name="record_detail"),
    path("<int:record_id>/edit/", views.record_edit_view, name="record_edit"),
    path("<int:record_id>/delete/", views.record_soft_delete_view, name="record_soft_delete"),
    path("bulk-delete/", views.records_bulk_delete_view, name="records_bulk_delete"),

    # Attachments
    path("<int:record_id>/attachments/upload/", views.attachment_upload_view, name="attachment_upload"),
    path("attachments/<int:attachment_id>/download/", views.attachment_download_view, name="attachment_download"),
    path("attachments/<int:attachment_id>/delete/", views.attachment_delete_view, name="attachment_delete"),
    path("attachments/<int:attachment_id>/pdf/", views.attachment_pdf_view, name="attachment_pdf"),
    
    

    # Excel helpers (optional extra routes)
    path("export/excel/", views.records_export_excel_view, name="records_export_excel"),
    path("import/excel/", views.records_import_excel_view, name="records_import_excel"),
    path("import/template/", views.import_template_download_view, name="import_template_download"),
]
