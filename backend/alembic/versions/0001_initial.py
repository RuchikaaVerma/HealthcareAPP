"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-29

This migration creates every table for the platform AND the partial unique
index that is the real enforcement mechanism behind double-booking
prevention: uq_doctor_slot_active only applies to rows where
status IN ('held', 'confirmed'), so a cancelled/completed appointment never
blocks rebooking that slot, but two simultaneously-held/confirmed
appointments for the same doctor+slot_start are physically impossible.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

user_role_enum = postgresql.ENUM(
    "admin",
    "doctor",
    "patient",
    name="userrole",
    create_type=False
)
appointment_status_enum = postgresql.ENUM(
    "held", "confirmed", "cancelled_by_patient", "cancelled_by_doctor",
    "cancelled_by_leave", "completed", "no_show", name="appointmentstatus",create_type=False
)
urgency_enum = postgresql.ENUM("Low", "Medium", "High", name="urgencylevel",create_type=False)
reminder_status_enum = postgresql.ENUM("pending", "sent", "failed", "cancelled", name="reminderstatus",create_type=False)
calendar_owner_enum = postgresql.ENUM("patient", "doctor", name="calendarownertype",create_type=False)
notification_type_enum = postgresql.ENUM(
    "booking_confirmation", "reminder", "cancellation", "leave_conflict",
    "medication_reminder", "reschedule", name="notificationtype",create_type=False
)
notification_status_enum = postgresql.ENUM("pending", "sent", "failed", "exhausted", name="notificationstatus",create_type=False)


def upgrade():
    bind = op.get_bind()
    user_role_enum.create(bind, checkfirst=True)
    appointment_status_enum.create(bind, checkfirst=True)
    urgency_enum.create(bind, checkfirst=True)
    reminder_status_enum.create(bind, checkfirst=True)
    calendar_owner_enum.create(bind, checkfirst=True)
    notification_type_enum.create(bind, checkfirst=True)
    notification_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "doctors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("specialisation", sa.String(150), nullable=False),
        sa.Column("bio", sa.String(1000), nullable=True),
        sa.Column("slot_duration_minutes", sa.Integer, nullable=False, server_default="30"),
        sa.Column("is_accepting_patients", sa.String(10), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_doctors_specialisation", "doctors", ["specialisation"])

    op.create_table(
        "working_hours",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.Integer, nullable=False),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_working_hours_doctor_id", "working_hours", ["doctor_id"])

    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("date_of_birth", sa.String(20), nullable=True),
        sa.Column("gender", sa.String(20), nullable=True),
        sa.Column("blood_group", sa.String(10), nullable=True),
        sa.Column("emergency_contact", sa.String(30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "leaves",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_leaves_doctor_id", "leaves", ["doctor_id"])

    op.create_table(
        "appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctors.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("slot_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("slot_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", appointment_status_enum, nullable=False, server_default="held"),
        sa.Column("hold_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("symptoms_text", sa.Text, nullable=True),
        sa.Column("ai_urgency_level", urgency_enum, nullable=True),
        sa.Column("ai_chief_complaint", sa.Text, nullable=True),
        sa.Column("ai_suggested_questions", sa.Text, nullable=True),
        sa.Column("ai_pre_visit_raw", sa.Text, nullable=True),
        sa.Column("ai_pre_visit_failed", sa.Integer, server_default="0"),
        sa.Column("doctor_notes", sa.Text, nullable=True),
        sa.Column("prescription_text", sa.Text, nullable=True),
        sa.Column("ai_post_visit_summary", sa.Text, nullable=True),
        sa.Column("ai_post_visit_failed", sa.Integer, server_default="0"),
        sa.Column("cancellation_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_slot_start", "appointments", ["slot_start"])
    op.create_index("ix_appointments_status", "appointments", ["status"])

    # --- THE critical constraint: prevents double-booking at the DB level ---
    op.execute("""
        CREATE UNIQUE INDEX uq_doctor_slot_active
        ON appointments (doctor_id, slot_start)
        WHERE status IN ('held', 'confirmed')
    """)

    op.create_table(
        "reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("appointment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("drug_name", sa.String(255), nullable=False),
        sa.Column("dosage", sa.String(100), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", reminder_status_enum, nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reminders_appointment_id", "reminders", ["appointment_id"])
    op.create_index("ix_reminders_due_at", "reminders", ["due_at"])
    op.create_index("ix_reminders_status", "reminders", ["status"])

    op.create_table(
        "calendar_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("appointment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_type", calendar_owner_enum, nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("google_event_id", sa.String(255), nullable=True),
        sa.Column("sync_failed", sa.String(10), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_calendar_events_appointment_id", "calendar_events", ["appointment_id"])

    op.create_table(
        "google_oauth_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("access_token", sa.String(2048), nullable=False),
        sa.Column("refresh_token", sa.String(2048), nullable=True),
        sa.Column("token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scope", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "notification_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("appointment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("appointments.id", ondelete="CASCADE"), nullable=True),
        sa.Column("recipient_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_email", sa.String(255), nullable=False),
        sa.Column("notification_type", notification_type_enum, nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("body_preview", sa.Text, nullable=True),
        sa.Column("status", notification_status_enum, nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer, server_default="0"),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notification_logs_appointment_id", "notification_logs", ["appointment_id"])
    op.create_index("ix_notification_logs_status", "notification_logs", ["status"])


def downgrade():
    op.drop_table("notification_logs")
    op.drop_table("google_oauth_tokens")
    op.drop_table("calendar_events")
    op.drop_table("reminders")
    op.execute("DROP INDEX IF EXISTS uq_doctor_slot_active")
    op.drop_table("appointments")
    op.drop_table("leaves")
    op.drop_table("patients")
    op.drop_table("working_hours")
    op.drop_table("doctors")
    op.drop_table("users")

    bind = op.get_bind()
    notification_status_enum.drop(bind, checkfirst=True)
    notification_type_enum.drop(bind, checkfirst=True)
    calendar_owner_enum.drop(bind, checkfirst=True)
    reminder_status_enum.drop(bind, checkfirst=True)
    urgency_enum.drop(bind, checkfirst=True)
    appointment_status_enum.drop(bind, checkfirst=True)
    user_role_enum.drop(bind, checkfirst=True)
