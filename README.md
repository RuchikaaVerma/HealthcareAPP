# Healthcare Appointment & Follow-up Manager

A full-stack healthcare appointment platform with separate patient, doctor, and admin experiences. Patients search doctors, book slots, and submit symptoms before a visit; an LLM (Google Gemini) generates a triage summary for the doctor. After the visit, the doctor's notes and prescription are converted into a patient-friendly summary, medication reminders are scheduled automatically, and both sides stay in sync via email and Google Calendar.

## Stack

- **Backend**: FastAPI (Python 3.12), PostgreSQL, SQLAlchemy, Alembic
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, React Three Fiber (3D), Framer Motion
- **LLM**: Google Gemini (`gemini-1.5-flash` by default)
- **Email**: SMTP via `fastapi-mail` (works with SendGrid, Mailgun SMTP relay, Gmail SMTP, etc.)
- **Calendar**: Google Calendar API with OAuth 2.0
- **Background jobs**: APScheduler (in-process, async)

## Project Structure

```
healthcare-app/
├── backend/
│   ├── app/
│   │   ├── core/          # config, database, security, auth dependencies
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── routers/       # API route handlers
│   │   ├── services/      # business logic (booking, LLM, email, calendar, leave, reminders, scheduler)
│   │   ├── main.py        # FastAPI app entrypoint
│   │   └── seed.py        # creates the initial admin account
│   ├── alembic/            # database migrations (includes the double-booking-prevention index)
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── app/            # Next.js App Router pages (login, register, patient, doctor)
    │   ├── components/     # shared UI, including the 3D vitals-orb hero scene
    │   └── lib/             # API client (with auto token refresh) and auth state
    ├── package.json
    └── .env.example
```

## Setup Guide

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+ (a free instance from Neon, Render, Railway, or Supabase works fine)
- A Google Cloud project with the Calendar API enabled and OAuth 2.0 credentials
- A Google Gemini API key (from Google AI Studio)
- An SMTP provider (SendGrid, Mailgun, or even a Gmail App Password for testing)

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: set DATABASE_URL, GEMINI_API_KEY, MAIL_* vars, GOOGLE_CLIENT_ID/SECRET, SECRET_KEY

# Apply the database schema (includes the partial unique index that prevents double-booking)
alembic upgrade head

# Create the initial admin account
SEED_ADMIN_EMAIL=admin@yourclinic.com SEED_ADMIN_PASSWORD=ChooseAStrongPassword python -m app.seed

# Run the API
python -m uvicorn app.main:app --reload
```

The API is now at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local: set NEXT_PUBLIC_API_BASE_URL to your backend URL

npm run dev
```

The app is now at `http://localhost:3000`.

### 3. Google Calendar Setup

1. In the [Google Cloud Console](https://console.cloud.google.com/), create a project (or use an existing one) and enable the **Google Calendar API**.
2. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**, application type **Web application**.
3. Add an authorized redirect URI matching your backend's `GOOGLE_REDIRECT_URI` (e.g. `http://localhost:8000/api/calendar/oauth/callback` for local dev, or your deployed backend URL in production).
4. Copy the generated **Client ID** and **Client Secret** into the backend `.env` as `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
5. While your app is in "Testing" publishing status, add the Google accounts you'll use for testing as **Test users** under the OAuth consent screen, or publish the app for general use.
6. In the frontend, a user (patient or doctor) connects their calendar by hitting `GET /api/calendar/oauth/start` (wire this to a "Connect Google Calendar" button), which redirects to Google's consent screen and back.

### 4. Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and create an API key.
2. Set it as `GEMINI_API_KEY` in the backend `.env`.
3. If the key is missing or Gemini is unreachable, the system does **not** break — pre-visit and post-visit summaries gracefully fall back to a safe default message, and the relevant `ai_*_failed` flag is set so the UI can show "AI summary unavailable."

### 5. Email (SMTP)

Works with any SMTP provider. Example for SendGrid:

```
MAIL_USERNAME=apikey
MAIL_PASSWORD=<your-sendgrid-api-key>
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
```
## Admin Login
Email: admin@clinic.com
Password: ChangeMe123!

Failed sends are logged to the `notification_logs` table and automatically retried by the background scheduler (up to `EMAIL_MAX_RETRIES` times), so a transient outage never silently drops a booking confirmation.

## Deployment

- **Backend**: deploy as a standard ASGI app on Render, Railway, or Fly.io (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`). Run `alembic upgrade head` as a release/pre-deploy step. Provision a managed Postgres instance (Render, Neon, Railway all offer free tiers).
- **Frontend**: deploy on Vercel (zero-config for Next.js) or Render. Set `NEXT_PUBLIC_API_BASE_URL` to your deployed backend's public URL.
- **CORS**: update `CORS_ORIGINS` in the backend `.env` to include your deployed frontend's URL.
- **Google OAuth redirect URI**: update both the Google Cloud Console credential and `GOOGLE_REDIRECT_URI` in `.env` to your deployed backend's callback URL once live.

## API Documentation

Full interactive API docs (OpenAPI/Swagger) are auto-generated and served at `/docs` once the backend is running. Below is a summary of the key endpoints.

### Auth (`/api/auth`)
| Method | Path | Description |
|---|---|---|
| POST | `/register` | Patient self-registration (admins cannot self-register) |
| POST | `/login` | Returns access + refresh JWT tokens |
| POST | `/refresh` | Exchanges a refresh token for a new access token |
| GET | `/me` | Returns the current authenticated user |

### Admin (`/api/admin`) — admin role required
| Method | Path | Description |
|---|---|---|
| POST | `/doctors` | Create a doctor account + profile + working hours |
| GET | `/doctors` | List all doctors |
| PATCH | `/doctors/{id}` | Update a doctor's profile |
| POST | `/doctors/{id}/leave` | Mark a doctor on leave; auto-cancels and notifies affected patients |

### Doctors (`/api/doctors`) — public/patient-facing
| Method | Path | Description |
|---|---|---|
| GET | `/` | Search doctors, optionally by specialisation |
| GET | `/{id}/slots?date=YYYY-MM-DD` | Get available slots for a doctor on a given day |

### Appointments (`/api/appointments`)
| Method | Path | Description |
|---|---|---|
| POST | `/hold` | Patient reserves a slot (HELD status, the "slot hold" mechanism) |
| POST | `/confirm` | Patient submits symptoms; LLM generates pre-visit summary; booking is confirmed; email + calendar sync fires |
| GET | `/me` | List the current user's appointments (patient or doctor) |
| GET | `/{id}` | Get a single appointment (role-checked) |
| POST | `/{id}/cancel` | Cancel an appointment |
| POST | `/post-visit` | Doctor submits notes + prescription; LLM generates patient-friendly summary; medication reminders are scheduled |

### Calendar (`/api/calendar`)
| Method | Path | Description |
|---|---|---|
| GET | `/oauth/start` | Returns the Google consent URL for the current user |
| GET | `/oauth/callback` | OAuth redirect target; stores tokens |
| GET | `/status` | Whether the current user has linked their calendar |

## Database Schema

See `backend/alembic/versions/0001_initial.py` for the full schema. Key tables:

- **users** — shared auth table for admin/doctor/patient, with role column
- **doctors** / **working_hours** — doctor profile and weekly availability template
- **patients** — patient profile
- **leaves** — doctor unavailability date ranges
- **appointments** — the core transactional table; holds slot timing, status, AI pre/post-visit data, and prescription data. A partial unique index `uq_doctor_slot_active` on `(doctor_id, slot_start)` — scoped to `status IN ('held', 'confirmed')` — is what actually prevents double-booking at the database level (see the System Design doc for the full rationale).
- **reminders** — individual scheduled medication reminder doses, expanded from a prescription
- **calendar_events** — tracks the Google Calendar event ID created for each appointment, per owner (patient/doctor), so it can be updated or deleted correctly
- **google_oauth_tokens** — stores each user's Google OAuth tokens
- **notification_logs** — every outbound email is logged here before sending, enabling reliable retries

## LLM Prompts

**Pre-visit summary** (triggered on booking confirmation):
> "You are a clinical triage assistant... Analyse the symptoms below and respond with STRICT JSON: urgency_level (Low/Medium/High), chief_complaint, suggested_questions (3 questions). Symptoms: `<symptoms>`"

**Post-visit summary** (triggered when the doctor submits notes):
> "You are a medical assistant converting clinical notes into a patient-friendly summary... Respond with STRICT JSON: summary, medication_schedule, follow_up_steps. Clinical notes: `<notes>` Prescriptions: `<prescriptions>`"

Full prompt templates are in `backend/app/services/llm_service.py`.

## Design Highlights

- **Double-booking prevention**: enforced at the database level via a Postgres partial unique index, not just application logic — see `SYSTEM_DESIGN.md` for the full writeup.
- **Slot hold mechanism**: a slot is reserved as `HELD` while a patient fills the symptom form, with a short expiry (`SLOT_HOLD_EXPIRY_SECONDS`); abandoned holds are swept by the background scheduler every minute.
- **Leave conflict handling**: marking a doctor on leave automatically cancels affected appointments and notifies patients in one atomic flow.
- **Graceful LLM failure handling**: every LLM call is wrapped in retries with exponential backoff; on exhaustion, a safe fallback message is stored and a `*_failed` flag is set, so booking and visit-completion never break.
- **Reliable notifications**: every email is logged before sending; failures are retried automatically by a background job rather than silently dropped.
- **3D, animated UI**: a calm, clinical-but-distinctive visual identity (deep navy + teal palette, Space Grotesk/Inter typography) anchored by a React Three Fiber "vitals orb" hero scene.

## Known Limitations / Next Steps

- The in-process APScheduler is appropriate for a single backend instance; a multi-instance production deployment should move background jobs to a dedicated worker (e.g. Celery + Redis) to avoid duplicate job execution.
- OAuth tokens are stored in plaintext in `google_oauth_tokens`; production deployments should encrypt them at rest.
- No automated test suite is included in this deliverable; given the scope, adding pytest coverage for the slot/booking concurrency logic would be the highest-value next addition.
