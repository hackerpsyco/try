import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


# =========================
# STUDENT
# =========================
class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment_number = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[("M", "Male"), ("F", "Female")]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


# =========================
# ENROLLMENT
# =========================
class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="enrollments"
    )
    school = models.ForeignKey(
        "class.School", on_delete=models.CASCADE, related_name="enrollments"
    )
    class_section = models.ForeignKey(
        "class.ClassSection", on_delete=models.CASCADE, related_name="enrollments"
    )

    start_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("student", "class_section", "is_active")

    def save(self, *args, **kwargs):
        if not self.school and self.class_section:
            self.school = self.class_section.school
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} → {self.class_section}"



# =========================
# PLANNED SESSION (DAY LEVEL)
# =========================
class PlannedSession(models.Model):
    """
    Represents ONE logical teaching day (Day 1, Day 2, ...)
    Imported from curriculum CSV
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class_section = models.ForeignKey(
        "class.ClassSection",
        on_delete=models.CASCADE,
        related_name="planned_sessions"
    )

    day_number = models.PositiveIntegerField(
        help_text="Logical day number (Day 1, Day 2, ...)"
    )

    title = models.CharField(
        max_length=255,
        help_text="Session title (e.g. CLAS - Computer Literacy At School)"
    )

    description = models.TextField(
        blank=True,
        help_text="Optional day-level description"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["day_number"]
        unique_together = ("class_section", "day_number")
        verbose_name = "Planned Session (Day)"
        verbose_name_plural = "Planned Sessions (Days)"

    def __str__(self):
        return f"{self.class_section} - Day {self.day_number}"


# =========================
# SESSION STEP (ACTIVITIES INSIDE DAY)
# =========================
class SessionStep(models.Model):
    """
    Represents ONE activity/step inside a day
    Example: English rhyme, Math activity, Computer video, etc.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    planned_session = models.ForeignKey(
        PlannedSession,
        on_delete=models.CASCADE,
        related_name="steps"
    )

    order = models.PositiveIntegerField(
        help_text="Execution order inside the day (1, 2, 3...)"
    )

    subject = models.CharField(
        max_length=30,
        choices=[
            ("english", "English"),
            ("hindi", "Hindi"),
            ("maths", "Maths"),
            ("computer", "Computer"),
            ("activity", "Activity / Energizer"),
            ("mindfulness", "Mindfulness"),
        ]
    )

    title = models.CharField(
        max_length=255,
        help_text="Activity title (from CSV 'What' column)"
    )

    description = models.TextField(
        blank=True,
        help_text="Detailed teacher instructions"
    )

    youtube_url = models.URLField(
        blank=True,
        null=True,
        help_text="Optional YouTube video for this step"
    )

    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Duration in minutes"
    )

    class Meta:
        ordering = ["order"]
        unique_together = ("planned_session", "order")
        verbose_name = "Session Step"
        verbose_name_plural = "Session Steps"

    def __str__(self):
        return f"Day {self.planned_session.day_number} - Step {self.order}"


# =========================
# ACTUAL SESSION (CALENDAR EXECUTION)
# =========================
class ActualSession(models.Model):
    """
    Represents REAL execution of a PlannedSession on a calendar date
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    planned_session = models.ForeignKey(
        PlannedSession,
        on_delete=models.CASCADE,
        related_name="actual_sessions"
    )

    date = models.DateField()

    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conducted_sessions"
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("conducted", "Conducted"),
            ("holiday", "Holiday"),
            ("cancelled", "Cancelled"),
        ],
        default="conducted"
    )

    remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("planned_session", "date")
        verbose_name = "Actual Session"
        verbose_name_plural = "Actual Sessions"

    def __str__(self):
        return f"{self.planned_session} on {self.date}"


class Attendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    actual_session = models.ForeignKey(
        ActualSession,
        on_delete=models.CASCADE,
        related_name="attendances"
    )

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="attendances"
    )

    status = models.CharField(
        max_length=10,
        choices=[
            ("present", "Present"),
            ("absent", "Absent"),
        ]
    )

    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("actual_session", "enrollment")

    def clean(self):
        if self.actual_session.status != "conducted":
            raise ValidationError("Attendance can only be marked for conducted sessions.")

    def __str__(self):
        return f"{self.enrollment} - {self.status}"
