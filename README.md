<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0B1220?style=for-the-badge&logo=fastapi&logoColor=13B8A6" />
  <img src="https://img.shields.io/badge/Next.js_14-0B1220?style=for-the-badge&logo=next.js&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-0B1220?style=for-the-badge&logo=postgresql&logoColor=7C9CFF" />
  <img src="https://img.shields.io/badge/Google_Gemini-0B1220?style=for-the-badge&logo=google&logoColor=FF6B6B" />
  <img src="https://img.shields.io/badge/React_Three_Fiber-0B1220?style=for-the-badge&logo=three.js&logoColor=white" />
</p>

<h1 align="center">⚕ Vitalis — Healthcare Appointment & Follow-up Manager</h1>

<p align="center">
  A full-stack clinic platform with AI-powered symptom triage, automated medication reminders,<br/>
  and real-time Google Calendar sync. Three portals: <strong>Patient · Doctor · Admin</strong>
</p>

<p align="center">
  <a href="#-quickstart">Quickstart</a> ·
  <a href="#-api-endpoints">API Docs</a> ·
  <a href="#-database-schema">DB Schema</a> ·
  <a href="#-llm-prompts">LLM Prompts</a> ·
  <a href="#-google-calendar-setup">Calendar Setup</a> ·
  <a href="#-deployment">Deployment</a>.
  <a href="https://drive.google.com/file/d/1HFI7YUNRZw-c5KyrPShjyLVXtf9tGd6K/view?usp=sharing-deployment">ZIP</a>.
  <a href="https://drive.google.com/file/d/1X2kukzUVyRnzcTOpGI1_yHAYQvsoF4Y7/view?usp=sharing-deployment">Demo</a>
  
</p>

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI (Python 3.12), SQLAlchemy, Alembic, APScheduler |
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS, React Three Fiber, Framer Motion |
| **Database** | PostgreSQL 14+ with partial unique index for concurrency safety |
| **LLM** | Google Gemini `gemini-1.5-flash` with retry + graceful fallback |
| **Email** | SMTP via `fastapi-mail` — works with Gmail, SendGrid, Mailgun |
| **Calendar** | Google Calendar API with OAuth 2.0 per-user token storage |
| **Auth** | JWT (HS256) with access + refresh token rotation |

---

## Project Structure

```
healthcare-appointment-manager/
├── README.md
├── SYSTEM_DESIGN.md
│
├── backend/
│   ├── app/
│   │   ├── core/            # config · database · security · auth deps
│   │   ├── models/          # SQLAlchemy ORM (9 tables)
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── routers/         # auth · admin · doctors · appointments · calendar
│   │   ├── services/        # slot · llm · email · calendar · leave · reminder · scheduler
│   │   ├── main.py          # FastAPI app entrypoint
│   │   └── seed.py          # creates the initial admin account
│   ├── alembic/
│   │   └── versions/
│   │       └── 0001_initial.py   # full schema + double-booking partial index
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    ├── src/
    │   ├── app/             # pages: login · register · patient · doctor
    │   ├── components/
    │   │   ├── 3d/          # VitalsOrb · OrbScene · ParticleField (React Three Fiber)
    │   │   └── ui/          # Button · GlassCard · FormFields · UrgencyBadge
    │   └── lib/             # api.ts (axios + JWT refresh) · authStore.ts (zustand)
    ├── package.json
    └── .env.example
```

---

## ⚡ Quickstart

> **Windows users:** replace `source venv/bin/activate` with `venv\Scripts\activate`

### 1 · Backend

```bash
cd healthcare-appointment-manager/backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env         # Windows
# cp .env.example .env         # Mac/Linux

# Edit .env — minimum required:
# DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
# SECRET_KEY=any_long_random_string
```

### 2 · Run Database Migrations

```bash
alembic upgrade head
```

> Creates all 9 tables including the `uq_doctor_slot_active` partial unique index that prevents double-booking at the database level.

### 3 · Seed Admin Account

```bash
# Windows CMD:
set SEED_ADMIN_EMAIL=admin@clinic.com
set SEED_ADMIN_PASSWORD=ChooseStrongPassword
python -m app.seed

# Run the API
uvicorn app.main:app --reload
```

→ API running at `http://localhost:8000`  
→ Interactive Swagger docs at `http://localhost:8000/docs`

### 5 · Frontend

```bash
cd ../frontend
npm install
copy .env.example .env.local   # Windows
npm run dev
```

→ App running at `http://localhost:3000`

> **Minimum to get running:** Only `DATABASE_URL` and `SECRET_KEY` are strictly required.
> Without Gemini/SMTP/Google keys — AI summaries show a graceful fallback, emails log to DB without sending, calendar sync is silently skipped. The app is fully usable.

---

## ⚙ Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ Required | Postgres connection string. Use `postgresql://` prefix. Add `?sslmode=require` for Neon/cloud. |
| `SECRET_KEY` | ✅ Required | Random string (32+ chars) used to sign JWTs. Never commit this. |
| `GEMINI_API_KEY` | Optional | From [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey). Without it, AI summaries show a fallback. |
| `GEMINI_MODEL` | Optional | Default: `gemini-1.5-flash` |
| `MAIL_USERNAME` | Optional | Your Gmail address or SMTP username |
| `MAIL_PASSWORD` | Optional | Gmail App Password (16-char) or SMTP API key |
| `MAIL_SERVER` | Optional | `smtp.gmail.com` for Gmail · `smtp.sendgrid.net` for SendGrid |
| `MAIL_PORT` | Optional | `587` for STARTTLS (recommended) |
| `GOOGLE_CLIENT_ID` | Optional | OAuth 2.0 client ID from Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | Optional | OAuth 2.0 client secret — keep private |
| `GOOGLE_REDIRECT_URI` | Optional | Default: `http://localhost:8000/api/calendar/oauth/callback` |
| `CORS_ORIGINS` | Optional | Default: `http://localhost:3000` |
| `SLOT_HOLD_EXPIRY_SECONDS` | Optional | Default: `120` — how long a slot hold lasts before auto-release |
| `SCHEDULER_INTERVAL_MINUTES` | Optional | Default: `5` — how often background jobs run |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | ✅ Required | Backend URL. Default: `http://localhost:8000` |

---

## 🔑 Google Calendar Setup

1. Go to [console.cloud.google.com](https://console.cloud.google.com) → create or select a project
2. **APIs & Services → Enable APIs** → enable **Google Calendar API**
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Application type: **Web application**
4. Add authorized redirect URI:
   ```
   http://localhost:8000/api/calendar/oauth/callback
   ```
5. Copy **Client ID** and **Client Secret** into backend `.env`
6. Under **OAuth consent screen → Test users** — add the Google accounts you'll use for testing
7. Users connect their calendar in-app via the "Connect Google Calendar" button which calls `GET /api/calendar/oauth/start`

> **How it works:** User consents → Google redirects to `/oauth/callback` → tokens stored per user in `google_oauth_tokens` table → events created/updated/deleted automatically on every booking action.

---

## 📧 Email Setup (Gmail SMTP)

1. Enable 2-Step Verification on your Google account
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Create an App Password — you get a 16-character code
4. Set in `.env`:

```env
MAIL_USERNAME=youraddress@gmail.com
MAIL_PASSWORD=abcdefghijklmnop    # 16-char app password, no spaces
MAIL_FROM=youraddress@gmail.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
```
## Admin Login
Email: admin@clinic.com
Password: ChangeMe123!

> Failed emails are logged to `notification_logs` and automatically retried up to `EMAIL_MAX_RETRIES` times by the background scheduler — no silent drops.

---

## 📡 API Endpoints

> Full interactive docs at `http://localhost:8000/docs` once the backend is running.

### Auth — `/api/auth`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Patient self-registration. Returns access + refresh tokens. |
| `POST` | `/api/auth/login` | Login for any role. Returns JWT tokens. |
| `POST` | `/api/auth/refresh` | Exchange refresh token for a new access token. |
| `GET` | `/api/auth/me` | Returns the currently authenticated user's profile. |

### Admin — `/api/admin` _(admin role required)_

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/admin/doctors` | Create a doctor account + profile + working hours in one call. |
| `GET` | `/api/admin/doctors` | List all doctors with profiles and schedules. |
| `PATCH` | `/api/admin/doctors/{id}` | Update a doctor's specialisation, bio, or slot duration. |
| `POST` | `/api/admin/doctors/{id}/leave` | Mark doctor on leave — auto-cancels affected bookings and emails patients. |

### Doctors — `/api/doctors` _(public)_

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/doctors` | Search doctors. Filter by `?specialisation=cardiology` |
| `GET` | `/api/doctors/{id}/slots?date=YYYY-MM-DD` | Returns available un-held, un-confirmed slots for a day. |

### Appointments — `/api/appointments`

| Method | Path | Role | Description |
|---|---|---|---|
| `POST` | `/api/appointments/hold` | Patient | Step 1: Reserve slot (HELD status + 120s expiry timer). |
| `POST` | `/api/appointments/confirm` | Patient | Step 2: Submit symptoms → Gemini triage → CONFIRMED → email + calendar. |
| `GET` | `/api/appointments/me` | Any | List current user's appointments. |
| `GET` | `/api/appointments/{id}` | Any | Get single appointment (role-checked). |
| `POST` | `/api/appointments/{id}/cancel` | Any | Cancel → delete calendar events → cancel reminders → send email. |
| `POST` | `/api/appointments/post-visit` | Doctor | Submit notes + Rx → Gemini patient summary → schedule medication reminders. |

### Calendar — `/api/calendar`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/calendar/oauth/start` | Returns Google consent URL. Redirect the user's browser here. |
| `GET` | `/api/calendar/oauth/callback` | Google redirects here. Stores tokens, redirects browser back to frontend. |
| `GET` | `/api/calendar/status` | Whether the current user has linked their Google Calendar. |

---

## 🗄 Database Schema

> Full migration: `backend/alembic/versions/0001_initial.py`

```
┌─────────────────────────────────────────────────────────────┐
│  users                                                       │
│  id (PK) · email (UNIQUE) · role (admin/doctor/patient)     │
│  hashed_password · full_name · phone · is_active            │
└──────────────┬──────────────────────┬───────────────────────┘
               │                      │
       ┌───────▼───────┐      ┌───────▼──────┐
       │    doctors     │      │   patients   │
       │  specialisation│      │  date_of_birth│
       │  slot_duration │      │  blood_group  │
       └──┬────────┬───┘      └──────┬────────┘
          │        │                 │
   ┌──────▼──┐ ┌───▼────┐    ┌──────▼──────────────────────────┐
   │ working │ │ leaves │    │         appointments             │
   │  _hours │ │        │    │  slot_start · slot_end · status  │
   └─────────┘ └────────┘    │  symptoms · ai_urgency_level     │
                              │  doctor_notes · prescription     │
                              │  ★ UNIQUE INDEX (doctor_id,      │
                              │    slot_start) WHERE status IN   │
                              │    ('held','confirmed')          │
                              └─────┬──────────────┬────────────┘
                                    │              │
                          ┌─────────▼──┐  ┌────────▼──────────┐
                          │  reminders │  │ notification_logs  │
                          │  drug_name │  │ type · status      │
                          │  due_at    │  │ retry_count        │
                          │  status    │  └────────────────────┘
                          └────────────┘
```

| Table | Purpose |
|---|---|
| `users` | Shared auth for all roles — admin, doctor, patient |
| `doctors` | Doctor profile: specialisation, bio, slot duration |
| `working_hours` | Weekly availability template (day + start/end time) |
| `patients` | Patient profile: DOB, blood group, emergency contact |
| `leaves` | Doctor unavailability date ranges |
| `appointments` | Core transaction table with full booking lifecycle |
| `reminders` | Individual medication reminder doses (expanded from Rx) |
| `calendar_events` | Google Calendar event IDs per appointment per user |
| `google_oauth_tokens` | OAuth tokens per user for Calendar API |
| `notification_logs` | Every outbound email logged before sending — enables retries |

> **The key constraint:** `uq_doctor_slot_active` is a **partial unique index** on `(doctor_id, slot_start)` scoped to `WHERE status IN ('held', 'confirmed')`. This prevents double-booking at the database level — no application-level race condition possible. Cancelled/completed rows fall outside the index so those slots are freely re-bookable.

---

## 🤖 LLM Prompts

### Pre-Visit Triage _(triggered on booking confirmation)_

```
You are a clinical triage assistant helping a doctor prepare for a patient visit.
Analyse the symptoms below and respond with STRICT JSON only, no markdown, in exactly this shape:
{
  "urgency_level": "Low" | "Medium" | "High",
  "chief_complaint": "<one sentence summary of the main problem>",
  "suggested_questions": ["<question 1>", "<question 2>", "<question 3>"]
}

Symptoms: {symptoms}
```

### Post-Visit Summary _(triggered when doctor submits notes)_

```
You are a medical assistant converting clinical notes into a patient-friendly summary.
Respond with STRICT JSON only, no markdown, in exactly this shape:
{
  "summary": "<plain-language explanation of what was found, 3-5 sentences>",
  "medication_schedule": "<plain-language dosage and timing for each medication>",
  "follow_up_steps": "<what the patient should do next, when to return or seek urgent care>"
}

Clinical notes: {notes}
Prescriptions (structured): {prescriptions}
```

> Full templates with retry logic in `backend/app/services/llm_service.py`
>
> **Failure handling:** Every call uses exponential-backoff retries (`LLM_MAX_RETRIES`). On exhaustion, a safe fallback message is stored and `ai_*_failed=1` is set. Booking and visit-completion flows are **never blocked** by an LLM error.

---

## 🚀 Deployment

### Backend — Render / Railway / Fly.io

```bash
# Start command:
uvicorn app.main:app --host 0.0.0.0 --port $PORT

# Pre-deploy / release command:
alembic upgrade head
```

### Frontend — Vercel

```bash
# Set environment variable in Vercel dashboard:
NEXT_PUBLIC_API_BASE_URL=https://your-backend.onrender.com
```

### Checklist before going live

- [ ] Update `CORS_ORIGINS` to your production frontend URL
- [ ] Update `GOOGLE_REDIRECT_URI` and Google Cloud Console redirect URI to production backend URL
- [ ] Set a strong `SECRET_KEY` — never use the default
- [ ] Reset Neon/Postgres password if it was ever shared or exposed
- [ ] Consider encrypting `google_oauth_tokens` at rest for HIPAA-adjacent compliance

---

## Known Limitations

- **APScheduler** runs in-process — fine for a single instance. For horizontal scaling, move background jobs to Celery + Redis.
- **OAuth tokens** are stored in plaintext — encrypt at rest before handling real patient data in production.
- **No automated tests** included — highest-value addition would be pytest coverage for the slot concurrency logic in `services/slot_service.py`.

---

## Admin Credentials (default seed)

```
Email:    admin@clinic.com
Password: ChangeMe123!
```

> Change these immediately after first login in any non-local environment.
