# System Design — Healthcare Appointment & Follow-up Manager

> 800-word write-up covering double-booking prevention, slot hold mechanism, doctor leave conflict handling, and notification failure handling.

---

## Table of Contents

1. [Double-Booking Prevention](#1-double-booking-prevention)
2. [Slot Hold Mechanism](#2-slot-hold-mechanism)
3. [Doctor Leave Conflict Handling](#3-doctor-leave-conflict-handling)
4. [Notification Failure Handling](#4-notification-failure-handling)
5. [Trade-offs & Future Hardening](#5-trade-offs--future-hardening)

---

## 1. Double-Booking Prevention

The core risk in any slot-booking system is two patients successfully reserving the same doctor slot under concurrent requests. A naive approach — query for existing bookings, then insert if none exist — has a **race window**: both requests can pass the check before either commits its insert.

```
❌ NAIVE (UNSAFE) — race condition possible
─────────────────────────────────────────────
  Request A           Request B
  ──────────          ──────────
  SELECT slot...      SELECT slot...
    → slot free ✓       → slot free ✓   ← both pass at same time
  INSERT booking      INSERT booking
    → success ✓         → success ✓     ← DOUBLE BOOKING 💥
```

This system closes that window with a **partial unique index** enforced entirely at the database level:

```sql
CREATE UNIQUE INDEX uq_doctor_slot_active
ON appointments (doctor_id, slot_start)
WHERE status IN ('held', 'confirmed');
```

```
✅ THIS SYSTEM — DB constraint kills the race
─────────────────────────────────────────────
  Request A           Request B
  ──────────          ──────────
  INSERT (held)       INSERT (held)
    → committed ✓       → IntegrityError 💥
                          → 409 Conflict
                          → "Slot just taken,
                             choose another"
```

PostgreSQL enforces this atomically per transaction — no application-level timing can create a gap. The booking service (`slot_service.hold_slot`) **does not trust** that a slot is free because `get_available_slots` said so a moment earlier; it attempts the insert directly and catches `IntegrityError`. The partial `WHERE` clause is what allows cancelled/completed appointments to free up the slot for rebooking — those rows fall outside the indexed set.

---

## 2. Slot Hold Mechanism

The booking flow requires patients to fill a symptom form before a booking is finalised. If every patient could see and click the same slot while another patient fills the form, the data race surfaces in the UI even though the DB constraint would catch it. The solution is a **two-step flow**:

```
Patient books a slot
        │
        ▼
┌───────────────────┐
│  POST /hold       │  ← Slot status = HELD
│                   │     hold_expires_at = now + 120s
│  DB unique index  │     Slot disappears from other
│  fires here ──────┼──►  patients' available list
└───────────────────┘
        │
        │  Patient fills symptom form (up to 120 seconds)
        │
        ▼
┌───────────────────────────┐
│  POST /confirm            │  ← Gemini generates pre-visit summary
│                           │     Status → CONFIRMED
│  Calendar events created  │     Email sent to patient + doctor
│  for patient + doctor ────┼──►  hold_expires_at = null
└───────────────────────────┘

If patient abandons the form:
        │
        ▼
┌───────────────────────────┐
│  Background job           │  ← Runs every 60 seconds
│  release_expired_holds()  │     Deletes HELD rows past expiry
│                           │     Slot becomes bookable again
└───────────────────────────┘
```

The hold itself participates in the same DB-level guarantee — a `HELD` slot is just as protected from double-booking as a `CONFIRMED` one.

---

## 3. Doctor Leave Conflict Handling

When an admin marks a doctor on leave, all existing bookings in that date range must be cancelled and patients notified. This is handled atomically by `leave_service.create_leave_and_resolve_conflicts`:

```
Admin creates leave (start_date → end_date)
              │
              ▼
     ┌─────────────────┐
     │  Insert Leave   │
     │  row into DB    │
     └────────┬────────┘
              │
              ▼
  Query all HELD / CONFIRMED
  appointments in date range
              │
              ├──► For each affected appointment:
              │
              │    ┌──────────────────────────────────┐
              │    │  1. Status → CANCELLED_BY_LEAVE  │
              │    │  2. Delete Google Calendar events│
              │    │     (patient + doctor calendars) │
              │    │  3. Cancel pending reminders     │
              │    │  4. Send patient email:          │
              │    │     "Your appointment needs      │
              │    │      rescheduling due to leave"  │
              │    └──────────────────────────────────┘
              │
              ▼
     Return count of affected
     appointments to admin UI
     → "3 appointments cancelled,
        patients notified"
```

No appointment is silently dropped — every cancellation goes through the same notification pipeline as a regular cancellation, with the same email logging and retry guarantees.

---

## 4. Notification Failure Handling

Email delivery is treated as **inherently unreliable**. A single SMTP call inside the request/response cycle that fails would silently drop a booking confirmation. The solution is a **log-before-send + background retry** pipeline:

```
Booking confirmed
      │
      ▼
┌─────────────────────────────────┐
│  Write NotificationLog row      │
│  status = PENDING               │  ← This happens FIRST
│  (even if SMTP fails, row exists│
│   and can be retried later)     │
└──────────────┬──────────────────┘
               │
               ▼
        Attempt SMTP send
               │
       ┌───────┴────────┐
       │                │
    Success           Failure
       │                │
       ▼                ▼
  status = SENT    status = FAILED
                   last_error = "..."
                        │
                        ▼
          ┌─────────────────────────┐
          │  Background job runs    │
          │  every 5 minutes        │
          │  retry_failed_          │
          │  notifications()        │
          │                         │
          │  retry_count < MAX  ────┼──► Re-attempt SMTP
          │  retry_count >= MAX ────┼──► status = EXHAUSTED
          │                         │    (visible to admin)
          └─────────────────────────┘
```

The same pattern applies to **Google Calendar sync** — each `CalendarEvent` row records whether the create/update/delete API call succeeded (`sync_failed` flag). If a user hasn't linked their calendar or the API call fails, the **appointment and email flows are never blocked** — calendar sync degrades gracefully.

The same **graceful degradation** applies to the LLM: if Gemini fails after all retries, a safe fallback message is stored and `ai_pre_visit_failed = 1` is set. The booking flow completes normally.

```
Notification reliability summary:
─────────────────────────────────
  SMTP fails once    → retry up to EMAIL_MAX_RETRIES times
  SMTP exhausted     → EXHAUSTED status, admin can see it
  Calendar fails     → sync_failed flag set, booking unaffected
  Gemini fails       → fallback text stored, ai_*_failed = 1
  Any of the above   → app never crashes, user never blocked
```

---

## 5. Trade-offs & Future Hardening

| Area | Current | Production Hardening |
|---|---|---|
| **Background jobs** | APScheduler in-process | Move to Celery + Redis for multi-instance deployments to avoid duplicate job execution |
| **OAuth tokens** | Stored in plaintext | Encrypt at rest with pgcrypto or application-level Fernet key |
| **Calendar sync** | Best-effort, fire-and-forget | Add a retry queue for failed calendar syncs (same pattern as email) |
| **Scheduler** | Single interval for all jobs | Separate intervals per job type (holds: 60s, reminders: 5min, retries: 10min) |
| **Test coverage** | None included | Add pytest suite for `slot_service.py` concurrency logic as highest priority |
