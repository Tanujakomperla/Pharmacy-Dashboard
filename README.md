# Pharmacy Student Dashboard (Django version)

Live, database-backed dashboard. No Excel anywhere.

* **Students** register / log in, fill their marks once (like a Google Form), see ONLY their own result, and join Pharmacy Week event sections.
* **Admin** logs in and sees every page: Overview, Submissions (who submitted / who is pending), Student Information, Academic Analysis, Statistics, Correlation, Prediction, Add Student, Pharmacy Week Events (participants per section), CSV export.
* Built with **Django** (ORM, built-in login, built-in admin site at `/django-admin/`), pandas, scikit-learn, Chart.js.

## Two databases
| Database | Holds | Environment variable |
|---|---|---|
| Users DB (Django `default`) | login accounts, passwords (hashed), sessions | `USERS_DATABASE_URL` |
| Student DB (`student_data`) | marks, event sections, event registrations | `DATABASE_URL` |

* Nothing set -> two local SQLite files (`db_users.sqlite3`, `db_students.sqlite3`). Good for your laptop.
* Only `DATABASE_URL` set -> one hosted PostgreSQL holds everything (simplest for deployment).
* Both set -> two separate hosted databases.

> Why a hosted database? Free web hosts (Render free) wipe their disk on every restart. A database kept on
> a different service (Neon, free) keeps the data forever.

---
## A. Run on your computer (VS Code, Windows PowerShell)
1. Unzip, then in VS Code: **File -> Open Folder** -> choose the folder that contains `manage.py`.
2. Terminal -> New Terminal, then:
```
py -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py setup_portal
python manage.py runserver
```
(If activation is blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, answer Y, activate again.)
3. Open http://127.0.0.1:8000
4. Admin login on your computer: `admin@pharmacy.local` / `Admin@12345`. Students click **Create an account**.

`setup_portal` creates the tables, the admin account and the starter Pharmacy Week sections. It is safe to run every time.

## B. Put it on GitHub
Run these inside the folder that contains `manage.py`:
```
git init
git add .
git commit -m "Django pharmacy dashboard"
git branch -M main
git remote add origin https://github.com/<your-username>/<new-repo-name>.git
git push -u origin main
```
(Create the empty repo on github.com first. Replace the `<...>` parts with your real names.)

## C. Free hosted database (Neon) - needed so data never disappears
1. https://neon.tech -> sign up -> **Create project**.
2. Copy the **connection string** (starts with `postgresql://`). Keep it secret.

## D. Deploy on Render
1. https://render.com -> **New -> Blueprint** (or New -> Web Service) -> pick your GitHub repo.
   * If you use Web Service: Build Command `bash build.sh`, Start Command `python manage.py setup_portal && gunicorn config.wsgi:application`.
2. Environment variables:
   * `DATABASE_URL` = the Neon connection string
   * `ADMIN_EMAIL` = your admin email
   * `ADMIN_PASSWORD` = a strong password (min 8 characters)
   * (optional) `STUDENT_SIGNUP_CODE` = a code students must type to register
   * (optional) `USERS_DATABASE_URL` = a second Neon database, to keep accounts separate
3. Deploy. Share the `https://....onrender.com` link. First open after idle takes ~1 minute (free tier sleeps) - data is NOT lost.

If the folder with `manage.py` is inside another folder in your repo, set Render **Root Directory** to it.

## E. If Render does not work
* **Railway / Koyeb / Fly.io**: same repo; build `pip install -r requirements.txt && python manage.py collectstatic --noinput`, start `python manage.py setup_portal && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`; same env vars.
* **PythonAnywhere (free)**: upload the code, create a virtualenv, add a Django web app; use SQLite files (they persist there). Free accounts may not reach Neon, so use the local SQLite default.
* **Your own laptop**: `python manage.py runserver 0.0.0.0:8000` and share your Wi-Fi IP (same network only).

## How to explain it to your sir
1. A student creates an account (Django `User`, password hashed) -> stored in the **users database**.
2. The marks form is validated (marks 0-100, CGPA 0-10, etc.) and saved through the Django ORM (`StudentRecord`) into the **student database**.
3. The dashboards read the database every time, so new submissions appear instantly.
4. Access control: a middleware (`config/middleware.py`) checks the role on every request. Students can only open their own pages; admin pages return 403 for students. The student database stores a plain `user_id` instead of a link, so the two databases stay independent.
5. Same sidebar everywhere because every page extends `templates/base.html`.

## Project map
```
manage.py
config/    settings.py (databases), routers.py (which model -> which DB), middleware.py (roles), jinja.py, urls.py
portal/    models.py (tables), records.py (marks logic), events.py, accounts.py, views.py, urls.py, admin.py
           management/commands/setup_portal.py (tables + admin + sections)
analysis/  statistics.py, correlation.py, read_data.py
templates/ all pages     static/ css + js
```

## Notes
* Students can edit their own submission (one record per account). Admin can delete a record so the student may resubmit.
* Class averages show to a student only after 5+ students have submitted (privacy).
* Prediction needs at least 10 students; with random/small data R² can be low.
