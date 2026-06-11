# MD Registry System

A Django-based office records management system for tracking incoming and outgoing documents, memos, invoices, attachments, approvals, and audit activity across departments.

This project is structured as a multi-app Django application backed by **Microsoft SQL Server** and designed for internal office use. It includes role-based access, sign-up approval, workflow requests, soft deletes, restores, Excel import/export, and audit logging.

---
## Live demo of the project 
The demo of the project is below:

[Click here to watch the MD Registry System demo](https://drive.google.com/file/d/1Mk6aVBWEpaLj4wwwmDC6DvcxDo40el_l/view?usp=drive_link)

## What this project does

The MD Registry System helps an office:

- register incoming and outgoing records
- track document movement between departments
- record dispatch and return status
- attach supporting files to records
- manage departments and external companies
- control access with user roles
- allow new users to request accounts through sign up
- allow Admin users to approve or reject new sign-up requests
- submit and review action requests
- audit important user activity
- import and export records through Excel
- support multiple users on the same office Wi-Fi network

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
- Filtering and sorting support for registry records
- Pagination support for large record lists

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

### 4. Accounts, roles, and sign-up approval

The project uses a custom account and role system using project database tables rather than Django’s default user model.

Supported roles include:

- **Admin**
- **Clerk**
- **Viewer**

Account capabilities include:

- login/logout
- profile page
- users list and detail pages
- create/edit users
- toggle user active status
- groups and permissions management
- role-aware template rendering via context processors

#### New sign-up flow

New users can create an account from:

```text
/accounts/signup/
```

When a new user signs up, their account is created as inactive:

```text
IsActive = False
```

That means the user cannot log in immediately.

The Admin must review the account from the user management page.

#### Admin approval flow

Admin users can open:

```text
/accounts/users/
```

Pending users are shown as:

```text
Pending Approval / Disabled
```

The Admin can then choose:

- **Approve / Enable** — activates the account and allows the user to log in
- **Reject** — deletes the pending sign-up account and prevents the user from logging in

The rejection action creates an audit log entry using:

```text
USER_SIGNUP_REJECTED
```

The sign-up approval system uses the existing `Users.IsActive` field, so no new database table is required for this feature.

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
- Tracks actions across records, accounts, sign-up approval, and workflow operations
- Login and logout events are audited
- Sign-up rejection events are audited

### 7. Import / export

- Import records from Excel
- Export filtered records to Excel
- Download import template
- Uses `openpyxl`

### 8. Multi-user office Wi-Fi access

The project can be used by multiple people on different computers at the same time when everyone is connected to the same office Wi-Fi network.

A common office setup is:

```text
Computer running Django project
        |
        |-- User 1 opens the system in a browser
        |-- User 2 opens the system in a browser
        |-- User 3 opens the system in a browser
        |
SQL Server database used by the Django project
```

Users should not each run separate copies of the project. Instead, the project should run on one main computer or office server, and everyone else should access that same running server through the computer’s local IP address.

Example:

```text
http://192.168.1.20:8000
```

### 9. UI layer

- Django templates
- Shared base layout, navbar, topbar, sidebar, footer, and messages partials
- Static JS files for module-specific behavior
- Static CSS including an admin-style corporate theme
- Public login and sign-up pages
- Admin user management pages with approval/rejection actions

---

## Tech stack

- **Backend:** Django 5.x
- **Database:** Microsoft SQL Server
- **Python packages currently listed:**
  - Django
  - Pillow
  - ReportLab
  - openpyxl
- **SQL Server support packages commonly required:**
  - mssql-django
  - pyodbc
- **Frontend:** HTML, Django Templates, CSS, JavaScript, Bootstrap-style UI
- **File handling:** media uploads for record attachments

---

## Project structure

```text
MDRegistry/
├── apps/
│   ├── accounts/        # Users, groups, permissions, login, signup, approval, profile/admin screens
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

- login and logout
- public sign-up page
- pending sign-up accounts
- Admin approval of sign-up accounts
- Admin rejection of sign-up accounts
- user profile
- users administration
- group/permission screens
- role detection via session-based current user lookup

Important account routes include:

```text
/accounts/login/
/accounts/signup/
/accounts/logout/
/accounts/profile/
/accounts/users/
/accounts/users/create/
/accounts/users/<user_id>/
/accounts/users/<user_id>/edit/
/accounts/users/<user_id>/toggle-active/
/accounts/users/<user_id>/reject-signup/
```

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

```text
MDRegistryDB.bak
```

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

```text
Africa/Lagos
```

---

## Important setup note

The current `requirements.txt` includes only:

```txt
Django>=5.2
pillow
reportlab
openpyxl
```

But the project is configured to use SQL Server via:

```python
ENGINE = "mssql"
```

So in practice you will also need the SQL Server Django backend and ODBC support available in your environment.

Typical installations often include:

```bash
pip install mssql-django pyodbc
```

These packages may need to be added to `requirements.txt` if they are not already included.

---

## Local development setup

### 1. Create and activate a virtual environment

Open the project folder in VS Code or PowerShell, then run:

```bash
python -m venv venv
```

Activate the virtual environment on Windows PowerShell:

```bash
.\venv\Scripts\Activate.ps1
```

If your virtual environment is one level above the project folder, use:

```bash
..\venv\Scripts\Activate.ps1
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

### 4. Restore the included database backup

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

Example for local development:

```bash
set DJANGO_SECRET_KEY=change-me
set DJANGO_DEBUG=1
set DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

PowerShell example:

```powershell
$env:DJANGO_SECRET_KEY="change-me"
$env:DJANGO_DEBUG="1"
$env:DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost"
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

## Running the project for multiple users on the same office Wi-Fi

Use this section when all users are connected to the same office Wi-Fi and you want other computers to open the system from their browsers.

### 1. Find the host computer IPv4 address

On the computer where the Django project is running, open PowerShell and run:

```powershell
ipconfig
```

Look for the Wi-Fi adapter and find:

```text
IPv4 Address . . . . . . . . . . : 192.168.x.x
```

Example:

```text
192.168.1.20
```

### 2. Set `DJANGO_ALLOWED_HOSTS`

Your project reads `ALLOWED_HOSTS` from the environment variable `DJANGO_ALLOWED_HOSTS`.

Your settings pattern is:

```python
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip()
]
```

So you should not replace the whole `ALLOWED_HOSTS` line. Instead, set the environment variable.

PowerShell example:

```powershell
$env:DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost,192.168.1.20"
```

Replace `192.168.1.20` with your real IPv4 address.

### 3. Run Django on all network interfaces

Run:

```powershell
python manage.py runserver 0.0.0.0:8000
```

If Django shows:

```text
Starting development server at http://0.0.0.0:8000/
```

that is correct.

Users should not open `http://0.0.0.0:8000/`.

They should open the real IPv4 address of the host computer.

Example:

```text
http://192.168.1.20:8000
```

### 4. Allow access through Windows Firewall

If other computers cannot open the site:

1. Open **Windows Security**
2. Go to **Firewall & network protection**
3. Click **Allow an app through firewall**
4. Click **Change settings**
5. Find **Python**
6. Tick **Private**
7. Save

You can also allow port `8000` if needed.

### 5. Make sure the Wi-Fi network is private

On the host computer:

1. Open **Settings**
2. Go to **Network & Internet**
3. Open the connected Wi-Fi network
4. Set the network profile to **Private**

### 6. Important limitation

This office Wi-Fi setup works only while:

- the host computer is switched on
- the Django server is running
- all users are on the same office Wi-Fi
- Windows Firewall allows the connection

For more permanent office use, run the project on a dedicated office server or use a production server such as Waitress on Windows.

---

## Optional: Running with Waitress on Windows

For a more stable local office setup than Django’s development server, install Waitress:

```bash
pip install waitress
```

Then run:

```powershell
waitress-serve --listen=0.0.0.0:8000 config.wsgi:application
```

Users can then open:

```text
http://HOST_COMPUTER_IP:8000
```

Example:

```text
http://192.168.1.20:8000
```

---

## Sign-up approval workflow

### New user

1. Open the sign-up page:

```text
/accounts/signup/
```

2. Enter:
   - full name
   - username
   - email
   - password
   - confirm password

3. Submit the request.

The account is created but inactive:

```text
IsActive = False
```

The user must wait for Admin approval.

### Admin

1. Open:

```text
/accounts/users/
```

2. Find users marked:

```text
Pending Approval / Disabled
```

3. Choose one of the available actions:

```text
Approve / Enable
Reject
```

### If approved

The account becomes active:

```text
IsActive = True
```

The user can now log in.

### If rejected

The pending account is deleted.

An audit log is recorded:

```text
USER_SIGNUP_REJECTED
```

The rejected user cannot log in.

---

## URL areas

From the route configuration:

- `/` → records/home area
- `/dashboard/` → records dashboard
- `/table/` → records table
- `/create/` → create record
- `/accounts/` → authentication, sign-up, approval, and user administration
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
- `templates/accounts/login.html`
- `templates/accounts/signup.html`
- `templates/accounts/users_list.html`
- `templates/accounts/user_detail.html`
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
4. Do not use `ALLOWED_HOSTS=["*"]` for production.
5. Move database settings to environment variables.
6. Confirm SQL Server connection settings for the target machine.
7. Serve static files correctly from `STATIC_ROOT`.
8. Serve media files from a proper storage location.
9. Review attachment validation and upload limits.
10. Remove local machine-specific settings from source control.
11. Review the included `.env` and any secrets before publishing the repository.
12. Use HTTPS for public or internet-facing deployment.
13. Use a dedicated server or production WSGI server for long-term use.
14. Back up the SQL Server database regularly.

---

## Notable implementation details

- The project uses a custom session-based current user pattern via `request.session["user_id"]`.
- Role flags are injected globally into templates through context processors.
- Audit and workflow counts are also surfaced through context processors.
- The project includes custom 403, 404, and 500 templates.
- SQL Server table names are explicitly mapped in the models.
- New sign-up users are stored as inactive users until approved.
- Admin rejection of a sign-up request deletes the pending account.
- The local office multi-user setup uses `runserver 0.0.0.0:8000` and `DJANGO_ALLOWED_HOSTS`.

---

## Suggested next improvements

- Add a complete production-ready `requirements.txt`
- Add `mssql-django`, `pyodbc`, and `waitress` to the dependency list if they are required in your environment
- Move database host and connection settings to environment variables
- Add a `.env.example`
- Add automated tests
- Add seed/demo data instructions
- Add deployment instructions for Waitress, IIS, Docker, or Linux hosting
- Add screenshots to this README
- Document user roles and permission matrix in more detail
- Add record edit conflict protection for cases where two users edit the same record at the same time
- Add a dedicated sign-up request table if you later want to keep rejected request history without deleting pending users

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

MD Registry System is a Django + SQL Server office registry application built around records tracking, attachments, department routing, user roles, sign-up approval, sign-up rejection, workflow requests, soft deletes, restoration, Excel import/export, local office multi-user access, and auditing. It is structured well for internal office use and has room to be hardened for future production deployment and commercial packaging.
