# UG Feedback System

A production-ready undergraduate feedback management platform with role-based workflows for students and administrators, including faculty feedback, course-outcome surveys, eligibility controls, scheduled feedback windows, and audit logs.

## Tech Stack
<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-0E1117?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/MySQL-005C84?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL" />
  <img src="https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white" alt="Gunicorn" />
  <img src="https://img.shields.io/badge/Railway-131415?style=for-the-badge&logo=railway&logoColor=white" alt="Railway" />
</p>

## Core Features
- Student and admin authentication with `bcrypt` password hashing.
- Faculty feedback submission with one-response-per-student constraints.
- Course Outcome (CO) survey capture and history views.
- Admin controls for feedback periods (create, schedule, open, close, auto-activate).
- Student eligibility management (individual and bulk).
- Faculty-course assignment management.
- Reporting dashboards, faculty-level reports, and audit trail logging.

## Project Structure
```text
ug_feedback_system/
├── app.py                    # Flask app factory + blueprint registration
├── wsgi.py                   # Production WSGI entrypoint
├── config.py                 # Environment + DB configuration
├── requirements.txt          # Python dependencies
├── Procfile                  # Railway process definition
├── railway.json              # Railway start command
├── nixpacks.toml             # Explicit Railway/Nixpacks build plan
├── create_test_users.py      # Demo admin/student seeding
├── db/
│   └── connection.py         # MySQL connection + schema auto-init
├── routes/                   # Flask blueprints (auth, admin, student, ...)
├── services/                 # Business logic layer
├── sql/
│   └── schema.sql            # Full schema + seed data
├── templates/                # Jinja2 templates
└── static/                   # CSS and JS assets
```

## Database Model Highlights
`sql/schema.sql` creates and seeds:
- `students`, `admins`, `faculty`, `branches`, `courses`
- `student_enrollments`, `faculty_course_assignments`
- `feedback_periods`, `feedback_settings`
- `faculty_feedback`, `course_outcomes`, `course_outcome_survey`
- `audit_log`

The app auto-initializes schema on first DB connection via `db/connection.py`.

## Local Development Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create `.env` from `.env.example` and fill DB credentials.
4. Seed demo users:
   ```bash
   python create_test_users.py
   ```
5. Run the app:
   ```bash
   python app.py
   ```

## Demo Credentials
After running `create_test_users.py`:
- Admin: `admin` / `admin123`
- Student: `student@test.com` / `student123`

## Environment Variables
Use either standard DB vars or URL-style cloud vars.

```env
SECRET_KEY=replace-with-a-strong-random-value
DEBUG=False
SEED_TEST_USERS=false
ACADEMIC_YEAR=2025-26
SEMESTER=2

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=ug_feedback_db

# Optional URL format
# DATABASE_URL=mysql://user:password@host:3306/database
# MYSQL_URL=mysql://user:password@host:3306/database
```

## Deploy on Railway
1. Push this repository to GitHub.
2. Create a new Railway project from that repo.
3. Add a MySQL service in Railway.
4. Set environment variables in Railway:
   - `SECRET_KEY`
   - `DEBUG=False`
   - `SEED_TEST_USERS=true` (only for first deploy to create demo credentials, then set back to `false`)
   - `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`
   - or a single `DATABASE_URL`/`MYSQL_URL`
5. Deploy. Railway will run:
   - `./start.sh`

## Railway Deployment Checklist
- [ ] Repository pushed to GitHub.
- [ ] Railway project linked to this repository.
- [ ] MySQL service added in the same Railway project.
- [ ] Variables set: `SECRET_KEY`, `DEBUG=False`, `SEED_TEST_USERS=true`, and DB connection variables.
- [ ] First deploy completed with green status.
- [ ] Confirm test credentials work, then set `SEED_TEST_USERS=false`.
- [ ] Railway healthcheck passes on `/health`.
- [ ] Open app URL and verify admin login works.
- [ ] Open app URL and verify student login works.
- [ ] Open app URL and verify dashboard pages load without DB errors.

## Notes
- Feedback window availability is evaluated against current datetime and period status (`is_closed`).
- `before_request` auto-check activates scheduled periods during runtime.
- Health endpoint available at `/health` for Railway checks.
- Startup seeding is controlled by `SEED_TEST_USERS` in `start.sh`.
- Update `SECRET_KEY` and admin credentials before production usage.
