# MD Registry System

A Django-based office records management system for tracking incoming and outgoing documents, memos, invoices, and attachments across departments.

This project is structured as a multi-app Django application backed by **Microsoft SQL Server** and designed for internal office use, with a workflow layer for approvals, soft deletes, restores, and audit logging.

---

## What this project does

The MD Registry System helps an office:

- register incoming and outgoing records
- track document movement between departments
- record dispatch and return status
- attach supporting files to records
- manage departments and external companies
- control access with user roles
- submit and review action requests
- audit important user activity
- import and export records through Excel

---

## Main features

### 1. Records management

- Create, view, edit, and soft-delete records
- Store:
  - invoice number
  - messenger name
  - subject
  - description
  - date received
  - date dispatched
  - return status
  - date returned
  - status
  - incoming department
  - outgoing department
  - optional external-company details
- Bulk delete support
- Record detail page with related attachments and workflow context

### 2. Attachments

- Upload one or more files to a record
- Download attachments
- Delete attachments
- PDF view route for supported files
- Media files stored under the `media/` directory

### 3. Department and organization management

- Manage departments
- View department details
- Enable/disable department records
- Manage external company names used by records

### 4. Accounts and roles

Custom account and role system using project tables rather than Django’s default user model.

Supported role flow in the codebase includes:

- **Admin**
- **Clerk**
- **Viewer**

Capabilities include:

- login/logout
- profile page
- users list and detail pages
- create/edit users
- toggle user active status
- groups and permissions management
- role-aware template rendering via context processors

### 5. Workflow and approvals

- Submit action requests tied to records
- Review request details
- Approve or reject requests
- Compare pending requests for the same record
- Restore soft-deleted records
- Permanent delete workflow routes are present
- Deleted records list for review and recovery

### 6. Audit logging

- Audit dashboard
- Audit logs list and detail pages
- Logs linked to users, records, and requests
- Tracks actions across records and workflow operations

### 7. Import / export

- Import records from Excel
- Export filtered records to Excel
- Download import template
- Uses `openpyxl`

### 8. UI layer

- Django templates
- Shared base layout, navbar, topbar, sidebar, footer, and messages partials
- Static JS files for module-specific behavior
- Static CSS including an admin-style corporate theme

---

## Tech stack

- **Backend:** Django 5.x
- **Database:** Microsoft SQL Server
- **Python packages currently listed:**
  - Django
  - Pillow
  - ReportLab
  - openpyxl
- **Frontend:** HTML, Django Templates, CSS, JavaScript, Bootstrap-style UI
- **File handling:** media uploads for record attachments

---

## Project structure

```text
MDRegistry/
├── apps/
│   ├── accounts/        # Users, groups, permissions, login/profile/admin screens
│   ├── organization/    # Departments and external companies
│   ├── records/         # Main registry records, attachments, import/export
│   └── workflow/        # Requests, approvals, deleted records, audit logs
├── config/              # Django settings, URLs, WSGI/ASGI
├── static/              # CSS and JavaScript
├── templates/           # Shared and app templates
├── media/               # Uploaded files
├── logs/                # Application logs
├── manage.py
├── requirements.txt
└── MDRegistryDB.bak     # SQL Server backup file
```

---

## Core apps overview

### `apps.accounts`

Handles:

- authentication screens
- user profile
- users administration
- group/permission screens
- role detection via session-based current user lookup

### `apps.organization`

Handles:

- departments
- external companies

### `apps.records`

Handles:

- dashboard and home pages
- records table and filtering
- create/edit/detail/delete flows
- attachments
- Excel import/export

### `apps.workflow`

Handles:

- action requests
- request approval/rejection
- deleted records recovery
- audit dashboard and logs

---

## Database design notes

The project maps Django models directly to existing SQL Server tables using explicit `db_table` names.

Examples found in the codebase include:

- `Users`
- `Groups`
- `Permissions`
- `Departments`
- `Records`
- `RecordAttachments`
- `ActionRequests`
- `AuditLogs`
- `ExternalCompanyNames`

This suggests the project is intended to work with a predefined SQL Server schema rather than a typical greenfield Django-only schema.

A SQL Server backup file is included:

- `MDRegistryDB.bak`

---

## Database configuration currently in the project

The checked-in settings are configured for:

- **Database name:** `MDRegistryDB`
- **Engine:** `mssql`
- **Server:** `DESKTOP-A8L26RI\SQLEXPRESS`
- **Driver:** `ODBC Driver 18 for SQL Server`
- **Authentication:** Windows Authentication
- **Extra params:** `TrustServerCertificate=yes;`

The time zone in settings is:

- `Africa/Lagos`

---

## Important setup note

The current `requirements.txt` includes only:

```txt
Django>=5.2
pillow
reportlab
openpyxl
```

But the project is configured to use SQL Server via `ENGINE = "mssql"`, so in practice you will also need the SQL Server Django backend and ODBC support available in your environment.

Typical installations often include packages such as:

- `mssql-django`
- `pyodbc`

These are **not currently listed** in the checked-in `requirements.txt`, so make sure they are installed before running the project against SQL Server.

---

## Local development setup

### 1. Create and activate a virtual environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

If needed for SQL Server support:

```bash
pip install mssql-django pyodbc
```

### 3. Make sure SQL Server prerequisites are ready

You will need:

- Microsoft SQL Server installed and running
- ODBC Driver 18 for SQL Server installed
- the `MDRegistryDB` database restored or created
- the server name in `config/settings.py` changed to match your machine

### 4. Restore the included database backup (optional but likely intended)

A backup file is included at:

```text
MDRegistryDB.bak
```

Restore it in SQL Server Management Studio and ensure the database name is:

```text
MDRegistryDB
```

### 5. Review environment variables

The code supports these environment variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `MAX_ATTACHMENT_SIZE_BYTES`
- `MAX_IMPORT_SIZE_BYTES`
- `ALLOWED_ATTACHMENT_EXTS`

Example:

```bash
set DJANGO_SECRET_KEY=change-me
set DJANGO_DEBUG=1
set DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

### 6. Run migrations if needed

```bash
python manage.py makemigrations
python manage.py migrate
```

Because this project appears to map to an existing SQL Server schema, use migrations carefully if the database already exists and is already populated.

### 7. Start the development server

```bash
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

---

## URL areas

From the route configuration:

- `/` → records/home area
- `/dashboard/` → records dashboard
- `/table/` → records table
- `/create/` → create record
- `/accounts/` → authentication and user administration
- `/organization/` → departments and external companies
- `/workflow/` → requests, deleted records, and audit
- `/admin/` → Django admin

---

## Templates

The project contains app-level and shared templates, including:

- `templates/base/base.html`
- `templates/base/navbar.html`
- `templates/base/sidebar.html`
- `templates/base/topbar.html`
- `templates/base/footer.html`
- `templates/records/dashboard.html`
- `templates/records/records_table.html`
- `templates/records/record_form.html`
- `templates/records/record_detail.html`
- `templates/workflow/requests_list.html`
- `templates/workflow/request_detail.html`
- `templates/workflow/audit_dashboard.html`

---

## Static assets

### CSS

- `static/css/accounts.css`
- `static/css/admin_corporate.css`
- `static/css/styles.css`
- `static/css/workflow.css`

### JavaScript

- `static/js/accounts.js`
- `static/js/audit.js`
- `static/js/base.js`
- `static/js/main.js`
- `static/js/organization.js`
- `static/js/records.js`
- `static/js/workflow.js`

---

## Security and deployment notes

Before deploying this project to production:

1. Change the secret key.
2. Set `DEBUG=0`.
3. Set production `ALLOWED_HOSTS`.
4. Move database settings to environment variables.
5. Confirm SQL Server connection settings for the target machine.
6. Serve static files correctly from `STATIC_ROOT`.
7. Serve media files from a proper storage location.
8. Review attachment validation and upload limits.
9. Remove local machine-specific settings from source control.
10. Review the included `.env` and any secrets before publishing the repository.

---

## Notable implementation details

- The project uses a **custom session-based current user pattern** via `request.session["user_id"]`.
- Role flags are injected globally into templates through context processors.
- Audit and workflow counts are also surfaced through context processors.
- The project includes custom 403, 404, and 500 templates.
- SQL Server table names are explicitly mapped in the models.

---

## Suggested next improvements

- Add a complete production-ready `requirements.txt`
- Move database host and connection settings to environment variables
- Add a `.env.example`
- Add automated tests
- Add seed/demo data instructions
- Add deployment instructions for IIS, Docker, or Linux hosting
- Add screenshots to this README
- Document user roles and permission matrix in more detail

---

## Repository hygiene note

The uploaded project archive includes items that normally should be reviewed before sharing publicly, such as:

- `.env`
- `.git/`
- log files
- media uploads
- database backup file

That is fine for local development or backup purposes, but if this repository will be shared publicly, you should review those files carefully.

---

## License

No license file was found in the uploaded project.

If you plan to distribute or sell this software later, add an explicit license and ownership notice.

---

## Summary

MD Registry System is a Django + SQL Server office registry application built around records tracking, attachments, department routing, approvals, soft deletes, restoration, and auditing. It is structured well for internal office use and has room to be hardened for future production deployment and commercial packaging.
