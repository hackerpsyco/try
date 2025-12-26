# students/models.py
import uuid
from django.db import models

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
    
class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="enrollments"
    )

    class_section = models.ForeignKey(
        "class.ClassSection", on_delete=models.CASCADE, related_name="enrollments"
    )

    start_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("student", "class_section")

    def __str__(self):
        return f"{self.student} → {self.class_section}"



class PlannedSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class_section = models.ForeignKey(
        "class.ClassSection", on_delete=models.CASCADE, related_name="planned_sessions"
    )

    day_number = models.PositiveIntegerField()  # Day 1, Day 2, Day 3...
    topic = models.CharField(max_length=255)

    youtube_url = models.URLField(
        help_text="YouTube video URL for this session"
    )

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["day_number"]
        unique_together = ("class_section", "day_number")

    def __str__(self):
        return f"{self.class_section} - Day {self.day_number}"

from django.conf import settings

class ActualSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    planned_session = models.ForeignKey(
        PlannedSession, on_delete=models.CASCADE, related_name="actual_sessions"
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

    def __str__(self):
        return f"{self.planned_session} on {self.date}"

class Attendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    actual_session = models.ForeignKey(
        ActualSession, on_delete=models.CASCADE, related_name="attendances"
    )

    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=10,
        choices=[("present", "Present"), ("absent", "Absent")]
    )

    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("actual_session", "enrollment")

def today_session(request, class_section_id):
    class_section = get_object_or_404(ClassSection, id=class_section_id)

    planned_session = PlannedSession.objects.filter(
        class_section=class_section,
        is_active=True
    ).exclude(
        actual_sessions__status="conducted"
    ).order_by("day_number").first()

    return render(request, "facilitator/today_session.html", {
        "class_section": class_section,
        "planned_session": planned_session,
    })
