# Park Guide App Backend

Django REST backend for the Park Guide App

## Stack
- Django + Django REST Framework
- JWT authentication (SimpleJWT)
- Neon PostgreSQL
- Custom user model (`accounts.CustomUser`)
- Firebase secure file storage

## Current Features
- Course and module APIs
- Module completion tracking per user
- Course-level progress tracking per user
- Admin pages for courses, modules, module progress, and course progress

## Prerequisites
- Python 3.10+
- Project `.env` file from @MiyukiVigil
- Secrets files/credentials from @MiyukiVigil

Current configuration is environment-driven (see `park_guide/settings.py`):
- `DATABASE_URL` (Neon database URL)
- `DB_SSL_REQUIRE` (optional)
- `DB_CONN_MAX_AGE` (optional)
- `DB_CONN_HEALTH_CHECKS` (optional)

Email configuration (SMTP) is also environment-driven:
- `EMAIL_BACKEND` (default: `django.core.mail.backends.smtp.EmailBackend`)
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS`
- `EMAIL_USE_SSL`
- `DEFAULT_FROM_EMAIL`

Passkey configuration is environment-driven:
- `PASSKEY_RP_ID`
- `PASSKEY_RP_NAME`
- `PASSKEY_ORIGIN`
- `PASSKEY_ANDROID_PACKAGE_NAME`
- `PASSKEY_ANDROID_SHA256`

## Setup
1. Create and activate a virtual environment:

For Mac and Linux (Depnding on your terminal shell):
```bash
python -m venv venv
source venv/bin/activate
```

For Windows:
```bash
venv\Scripts\activate
```

2. Install backend dependencies:

```bash
pip install -r requirements.txt
```

3. Add required environment/secrets files provided by @MiyukiVigil:

- `.env`
- Firebase service account JSON (under `secrets/`)
- Any additional project secrets used by your environment

Example SMTP block in `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=your_email@gmail.com
```

Example passkey block in `.env`:

```env
PASSKEY_RP_ID=localhost
PASSKEY_RP_NAME=Park Guide App
PASSKEY_ORIGIN=http://localhost:3000
PASSKEY_ANDROID_PACKAGE_NAME=com.miyukivigil.parkguideapp
PASSKEY_ANDROID_SHA256=42:41:D6:FD:23:A2:3B:FD:5A:B9:86:3F:99:D5:2E:54:A3:D2:CF:4D:5C:B7:0A:EA:CC:52:31:B1:A4:AA:B7:55
```

Provider notes:
- Gmail: enable 2FA and create an App Password, then use that as `EMAIL_HOST_PASSWORD`.
- Outlook/Office365: `EMAIL_HOST=smtp.office365.com`, `EMAIL_PORT=587`, `EMAIL_USE_TLS=True`.

4. Run migrations:
For first time setup
```bash
python manage.py load_training_courses 
python manage.py makemigrations accounts courses
python manage.py migrate

```
After that when there's changes
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create admin user (to access admin dashboard):

```bash
python manage.py createsuperuser
```

6. Start server:

```bash
python manage.py runserver
```

Server URL:
- `http://127.0.0.1:8000` (For android dev build using physical phone, please set this: adb reverse tcp:8000 tcp:8000)

## API Base Paths
- App API root: `/api/`
- Auth API root: `/api/accounts/`
- Notifications API root: `/api/notifications/`
- User progress API root: `/api/user-progress/`
- Secure files API root: `/api/secure-files/`

## Authentication Endpoints
- `POST /api/accounts/register/` – register user
- `POST /api/accounts/login/` – get JWT `access` and `refresh`

All course/progress endpoints require `Authorization: Bearer <access_token>`.

## Training Endpoints
- `GET /api/courses/` – list courses with nested modules
- `GET /api/modules/` – list modules
- `GET /api/progress/` – list module progress rows for logged-in user
- `GET /api/course-progress/` – list course progress rows for logged-in user
- `POST /api/complete-module/` – mark module completed and auto-update course progress

## Notification Endpoints
- `GET /api/notifications/items/` – list notifications for logged-in user
- `POST /api/notifications/items/{id}/mark-read/` – mark one notification as read
- `POST /api/notifications/items/mark-all-read/` – mark all as read
- `POST /api/notifications/items/clear-read/` – delete all read notifications for user

All notification endpoints require `Authorization: Bearer <access_token>`.

## Secure File Endpoints (Firebase Storage)
- `GET /api/secure-files/files/` – list your uploaded files (admin sees all)
- `POST /api/secure-files/files/` – upload file with multipart field `file`
- `GET /api/secure-files/files/{id}/` – file metadata + temporary download URL
- `GET /api/secure-files/files/{id}/download-url/` – new temporary download URL
- `DELETE /api/secure-files/files/{id}/` – delete a file

All secure-file endpoints require `Authorization: Bearer <access_token>`.

## Firebase Setup

- Requires Firebase service account JSON file, request from @MiyukiVigil
```bash
python manage.py bootstrap_private_bucket
```

### Example `course-progress` response row

<<<<<<< HEAD
```json
{
  "id": 1,
  "user": 2,
  "course": 1,
  "completed_modules": 2,
  "total_modules": 5,
  "progress": 0.4,
  "completed": false,
  "updated_at": "2026-03-16T12:00:00Z"
}
```
=======
## API Overview
Base routes:
- `/api/`
- `/api/accounts/`
- `/api/notifications/`
- `/api/user-progress/`
- `/api/secure-files/`

Authentication:
- `POST /api/accounts/register/`
- `POST /api/accounts/login/`
- `POST /api/accounts/passkeys/login/options/`
- `POST /api/accounts/passkeys/login/verify/`
- `GET /api/accounts/passkeys/status/`
- `POST /api/accounts/passkeys/register/options/`
- `POST /api/accounts/passkeys/register/verify/`
- `POST /api/accounts/passkeys/disable/`
- `POST /api/accounts/token/refresh/`

Training:
- `GET /api/courses/`
- `GET /api/modules/`
- `GET /api/progress/`
- `POST /api/progress/`
- `GET /api/course-progress/`
- `POST /api/course-progress/`
- `POST /api/complete-module/`

Badges:
- `GET /api/user-progress/badges/`
- `GET /api/user-progress/my-badges/`

Notifications:
- `GET /api/notifications/items/`
- `POST /api/notifications/items/{id}/mark-read/`
- `POST /api/notifications/items/mark-all-read/`
- `POST /api/notifications/items/clear-read/`

Secure files:
- `GET /api/secure-files/files/`
- `POST /api/secure-files/files/` with multipart field `file`
- `GET /api/secure-files/files/{id}/`
- `DELETE /api/secure-files/files/{id}/`
- `GET /api/secure-files/files/{id}/download-url/`
- `GET /api/secure-files/files/{id}/download/`

All API endpoints require `Authorization: Bearer <access_token>` unless noted otherwise.
>>>>>>> 1c68695 (Fixes to various stuff)

## Admin
Open Django admin:
- `http://127.0.0.1:8000/admin/`

Available sections under Courses:
- Course
- Module

Available sections under User Progress:
- Module progress
- Course progress
- Badge
- User badge

Available sections under Secure Files:
- Secure files (includes drag-and-drop upload area in admin list page)

Available sections under Notifications:
- Notification
- User notification

Admin send flow:
1. Create a Notification in Django admin.
2. Select it from list view.
3. Run action: **Send selected notifications to all users**.

Demo badge setup command:
- `python manage.py seed_demo_badges` (creates selectable badges from current training courses/module data)

## Notes
- `ModuleProgress` and `CourseProgress` are the source of truth for learner progress.
- Admins can create badges and manage them with a pending workflow (`pending`, `granted`, `rejected`) based on each user's completed module count.
- Admin actions support syncing pending badges for eligible users, auto-approving pending badges, and auto-rejecting pending badges.
- Admins can also use a one-click action: **Sync pending then auto approve eligible users**.
- Notifications can be broadcast from admin to all regular app users in one action (excludes staff/admin accounts).
- New notifications created from admin are auto-broadcast immediately to all regular app users (no second step needed).
- Quiz data exists inside module content (`Module.quiz`) and now supports multiple quizzes per module.
- Training JSON can use either `quiz` (single object, backward compatible) or `quizzes` (array of quiz objects).
- Each quiz supports single-answer (`correctIndex`) and multi-answer (`correctIndexes`) with up to 3 correct choices.
- Posting to progress endpoints reuses and amends existing progress records for the same user/course or user/module instead of creating new IDs.
- Dependencies are maintained in `requirements.txt` and should stay project-focused only.
- Secure files are stored in Firebase private storage and accessed only with valid app auth + short-lived signed URLs.

## Azure Deployment Checklist

Required Azure App Service app settings:
- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS=<your-app-name>.azurewebsites.net`
- `DATABASE_URL=<your Neon connection string>`
- `DB_SSL_REQUIRE=True`
- `FIREBASE_STORAGE_BUCKET=<your firebase bucket>`
- `FIREBASE_SERVICE_ACCOUNT_JSON=<firebase service account json string>`

Startup command (App Service):
```bash
gunicorn park_guide.wsgi:application --bind=0.0.0.0 --timeout 600
```

Available sections under Notifications:
- Notification
- User notification

Admin send flow:
1. Create a Notification in Django admin.
2. Select it from list view.
3. Run action: **Send selected notifications to all users**.

Demo badge setup command:
- `python manage.py seed_demo_badges` (creates selectable badges from current training courses/module data)

## Notes
- `ModuleProgress` and `CourseProgress` are the source of truth for learner progress.
- Admins can create badges and manage them with a pending workflow (`pending`, `granted`, `rejected`) based on each user's completed module count.
- Admin actions support syncing pending badges for eligible users, auto-approving pending badges, and auto-rejecting pending badges.
- Admins can also use a one-click action: **Sync pending then auto approve eligible users**.
- Notifications can be broadcast from admin to all regular app users in one action (excludes staff/admin accounts).
- New notifications created from admin are auto-broadcast immediately to all regular app users (no second step needed).
- Quiz data exists inside module content (`Module.quiz`) and now supports multiple quizzes per module.
- Training JSON can use either `quiz` (single object, backward compatible) or `quizzes` (array of quiz objects).
- Each quiz supports single-answer (`correctIndex`) and multi-answer (`correctIndexes`) with up to 3 correct choices.
- Posting to progress endpoints reuses and amends existing progress records for the same user/course or user/module instead of creating new IDs.
- Dependencies are maintained in `requirements.txt` and should stay project-focused only.
- Secure files are stored in Firebase private storage and accessed only with valid app auth + short-lived signed URLs.
