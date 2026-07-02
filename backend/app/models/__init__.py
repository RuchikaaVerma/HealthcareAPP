"""Import every model so Base.metadata is fully populated for Alembic autogenerate."""
from app.models.user import User, UserRole               # noqa: F401
from app.models.doctor import Doctor, WorkingHours         # noqa: F401
from app.models.patient import Patient                     # noqa: F401
from app.models.appointment import Appointment, AppointmentStatus, UrgencyLevel  # noqa: F401
from app.models.leave import Leave                          # noqa: F401
from app.models.reminder import Reminder, ReminderStatus    # noqa: F401
from app.models.calendar_event import CalendarEvent, CalendarOwnerType  # noqa: F401
from app.models.google_token import GoogleOAuthToken        # noqa: F401
from app.models.notification_log import NotificationLog, NotificationType, NotificationStatus  # noqa: F401
