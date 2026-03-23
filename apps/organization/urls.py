from django.urls import path
from . import views

app_name = "organization"

urlpatterns = [
    path("departments/", views.departments_list_view, name="departments_list"),
    path("departments/create/", views.department_create_view, name="department_create"),
    path("departments/<int:department_id>/edit/", views.department_edit_view, name="department_edit"),
    path("departments/<int:department_id>/toggle-active/", views.department_disable_view, name="department_disable"),
    path("departments/<int:department_id>/", views.department_detail_view, name="department_detail"),
    path("external-companies/", views.external_companies_list_view, name="external_companies_list"),
    path("external-companies/<int:company_id>/", views.external_company_detail_view, name="external_company_detail"),
    path("external-companies/<int:company_id>/edit/", views.external_company_edit_view, name="external_company_edit"),
]
