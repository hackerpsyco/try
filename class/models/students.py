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
# PLANNED SESSION (DAY LEVEL) - ENHANCED
# =========================
class PlannedSession(models.Model):
    """
    Represents ONE logical teaching day (Day 1, Day 2, ...)
    Enhanced with sequence tracking and validation
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
    
    # New sequence management fields
    sequence_position = models.PositiveIntegerField(
        help_text="Enforced sequential position",
        null=True,
        blank=True
    )
    
    is_required = models.BooleanField(
        default=True,
        help_text="Cannot be skipped (default True)"
    )
    
    prerequisite_days = models.JSONField(
        default=list,
        blank=True,
        help_text="Days that must be completed first"
    )
    
    # Grouped session support
    grouped_session_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="If set, this session is part of a grouped session. All classes with same grouped_session_id share this session."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["day_number"]
        unique_together = ("class_section", "day_number")
        verbose_name = "Planned Session (Day)"
        verbose_name_plural = "Planned Sessions (Days)"
        indexes = [
            models.Index(fields=['class_section', 'day_number']),
            models.Index(fields=['class_section', 'is_active']),
        ]

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
# ACTUAL SESSION (CALENDAR EXECUTION) - ENHANCED
# =========================

# Cancellation reason choices
CANCELLATION_REASONS = [
    ('school_shutdown', 'School permanently shuts down for this class'),
    ('syllabus_change', 'Government removes topic from syllabus'),
    ('exam_period', 'Exam period replaces class permanently'),
    ('duplicate_session', 'Duplicate or wrongly created planned session'),
    ('emergency', 'Emergency where session will never happen again'),
]

class ActualSession(models.Model):
    """
    Represents REAL execution of a PlannedSession on a calendar date
    Enhanced with detailed status tracking and cancellation reasons
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
    
    # Enhanced tracking fields
    conducted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Exact time of conduct"
    )
    
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Session duration"
    )
    
    attendance_marked = models.BooleanField(
        default=False,
        help_text="Whether attendance was completed"
    )
    
    status_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="status_changes",
        help_text="Who changed the status"
    )
    
    status_change_reason = models.TextField(
        blank=True,
        help_text="Why status was changed"
    )
    
    can_be_rescheduled = models.BooleanField(
        default=True,
        help_text="For holiday sessions"
    )
    
    # Cancellation tracking
    cancellation_reason = models.CharField(
        max_length=50,
        choices=CANCELLATION_REASONS,
        blank=True,
        null=True,
        help_text="Predefined cancellation reasons"
    )
    
    cancellation_category = models.CharField(
        max_length=50,
        blank=True,
        help_text="school_shutdown, syllabus_change, exam_period, duplicate, emergency"
    )
    
    is_permanent_cancellation = models.BooleanField(
        default=False,
        help_text="Cannot be undone"
    )

    class Meta:
        unique_together = ("planned_session", "date")
        verbose_name = "Actual Session"
        verbose_name_plural = "Actual Sessions"
        indexes = [
            models.Index(fields=['planned_session', 'status']),
            models.Index(fields=['date', 'status']),
            models.Index(fields=['facilitator', 'date']),
        ]

    def __str__(self):
        return f"{self.planned_session} on {self.date}"
    
    def save(self, *args, **kwargs):
        # Set conducted_at when status changes to conducted
        if self.status == 'conducted' and not self.conducted_at:
            from django.utils import timezone
            self.conducted_at = timezone.now()
        
        # Set permanent cancellation flag
        if self.status == 'cancelled':
            self.is_permanent_cancellation = True
            self.can_be_rescheduled = False
        
        super().save(*args, **kwargs)


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
        max_length=15,
        choices=[
            ("present", "Present"),
            ("absent", "Absent"),
            ("leave", "Leave"),
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


# =========================
# SESSION BULK TEMPLATE - NEW
# =========================
class SessionBulkTemplate(models.Model):
    """
    Enhanced template model for bulk session generation
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(
        max_length=255,
        help_text="Template name (e.g., 'Standard CLAS Curriculum')"
    )
    
    description = models.TextField(
        help_text="Template description"
    )
    
    language = models.CharField(
        max_length=20,
        choices=[
            ('english', 'English'),
            ('hindi', 'Hindi'),
            ('both', 'Both'),
        ],
        default='english',
        help_text="Target language (Hindi/English/Both)"
    )
    
    total_days = models.PositiveIntegerField(
        default=150,
        help_text="Number of days in template (default 150)"
    )
    
    # Template structure
    day_templates = models.JSONField(
        default=dict,
        help_text="Day-wise content templates"
    )
    
    default_activities = models.JSONField(
        default=dict,
        help_text="Standard activities per day"
    )
    
    learning_objectives = models.JSONField(
        default=dict,
        help_text="Objectives for each day"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Administrator who created template"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether template can be used"
    )
    
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times applied"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Session Bulk Template"
        verbose_name_plural = "Session Bulk Templates"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.language})"


# =========================
# LESSON PLAN UPLOAD - NEW
# =========================
class LessonPlanUpload(models.Model):
    """
    New model to track facilitator lesson plan uploads
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    planned_session = models.ForeignKey(
        PlannedSession,
        on_delete=models.CASCADE,
        related_name="lesson_plan_uploads",
        help_text="Reference to the session"
    )
    
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lesson_plan_uploads",
        help_text="Who uploaded the lesson plan"
    )
    
    upload_date = models.DateField(
        auto_now_add=True,
        help_text="When it was uploaded"
    )
    
    lesson_plan_file = models.FileField(
        upload_to='lesson_plans/%Y/%m/',
        help_text="Uploaded lesson plan file"
    )
    
    file_name = models.CharField(
        max_length=255,
        help_text="Original file name"
    )
    
    file_size = models.PositiveIntegerField(
        help_text="File size in bytes"
    )
    
    upload_notes = models.TextField(
        blank=True,
        help_text="Optional notes from facilitator"
    )
    
    is_approved = models.BooleanField(
        default=False,
        help_text="Admin approval status"
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_lesson_plans",
        help_text="Admin who approved"
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Approval timestamp"
    )
    
    class Meta:
        unique_together = ('planned_session', 'facilitator')
        verbose_name = "Lesson Plan Upload"
        verbose_name_plural = "Lesson Plan Uploads"
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"Lesson Plan - {self.planned_session} by {self.facilitator.full_name}"


# =========================
# SESSION REWARD - NEW
# =========================
class SessionReward(models.Model):
    """
    New model to track student rewards
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    actual_session = models.ForeignKey(
        ActualSession,
        on_delete=models.CASCADE,
        related_name="rewards",
        help_text="Reference to the conducted session"
    )
    
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="session_rewards",
        help_text="Who gave the reward"
    )
    
    reward_type = models.CharField(
        max_length=20,
        choices=[
            ('photo', 'Photo'),
            ('text', 'Text'),
            ('both', 'Both'),
        ],
        default='text',
        help_text="photo, text, both"
    )
    
    reward_photo = models.ImageField(
        upload_to='session_rewards/%Y/%m/',
        null=True,
        blank=True,
        help_text="Photo of reward/student"
    )
    
    reward_description = models.TextField(
        help_text="Text description of reward"
    )
    
    student_names = models.TextField(
        help_text="Names of students who received rewards"
    )
    
    reward_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When reward was given"
    )
    
    is_visible_to_admin = models.BooleanField(
        default=True,
        help_text="Admin visibility"
    )
    
    admin_notes = models.TextField(
        blank=True,
        help_text="Admin comments on reward"
    )
    
    class Meta:
        ordering = ['-reward_date']
        verbose_name = "Session Reward"
        verbose_name_plural = "Session Rewards"
    
    def __str__(self):
        return f"Reward - {self.actual_session} by {self.facilitator.full_name}"


# =========================
# SESSION FEEDBACK - NEW
# =========================
class SessionFeedback(models.Model):
    """
    New model for comprehensive session feedback
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    actual_session = models.ForeignKey(
        ActualSession,
        on_delete=models.CASCADE,
        related_name="feedback",
        help_text="Reference to conducted session"
    )
    
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="session_feedback",
        help_text="Who provided feedback"
    )
    
    # Student Analysis Feedback
    student_engagement_level = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="1-5 scale"
    )
    
    student_understanding_level = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="1-5 scale"
    )
    
    student_participation_notes = models.TextField(
        blank=True
    )
    
    learning_objectives_met = models.BooleanField(
        default=True
    )
    
    challenging_topics = models.TextField(
        blank=True
    )
    
    student_questions = models.TextField(
        blank=True
    )
    
    # Session Progress Feedback
    session_completion_percentage = models.PositiveIntegerField(
        choices=[(i, f"{i}%") for i in range(0, 101, 10)],
        default=100,
        help_text="0-100%"
    )
    
    time_management_rating = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="1-5 scale"
    )
    
    content_difficulty_rating = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="1-5 scale"
    )
    
    # Facilitator Personal Reflection
    facilitator_satisfaction = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="1-5 scale"
    )
    
    what_went_well = models.TextField()
    
    areas_for_improvement = models.TextField()
    
    next_session_preparation = models.TextField(
        blank=True
    )
    
    additional_notes = models.TextField(
        blank=True
    )
    
    # Metadata
    feedback_date = models.DateTimeField(auto_now_add=True)
    
    is_complete = models.BooleanField(
        default=False,
        help_text="Whether all required fields are filled"
    )
    
    class Meta:
        unique_together = ('actual_session', 'facilitator')
        verbose_name = "Session Feedback"
        verbose_name_plural = "Session Feedback"
        ordering = ['-feedback_date']
    
    def __str__(self):
        return f"Feedback - {self.actual_session} by {self.facilitator.full_name}"


# =========================
# SESSION PREPARATION CHECKLIST - NEW
# =========================
class SessionPreparationChecklist(models.Model):
    """
    New model for session preparation tracking
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    planned_session = models.ForeignKey(
        PlannedSession,
        on_delete=models.CASCADE,
        related_name="preparation_checklists",
        help_text="Reference to session"
    )
    
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preparation_checklists",
        help_text="Who is preparing"
    )
    
    # Preparation Checkpoints
    lesson_plan_reviewed = models.BooleanField(default=False)
    materials_prepared = models.BooleanField(default=False)
    technology_tested = models.BooleanField(default=False)
    classroom_setup_ready = models.BooleanField(default=False)
    student_list_reviewed = models.BooleanField(default=False)
    previous_session_feedback_reviewed = models.BooleanField(default=False)
    
    # Checkpoint Timestamps
    checkpoints_completed_at = models.JSONField(
        default=dict,
        help_text="Track when each checkpoint was completed"
    )
    
    preparation_start_time = models.DateTimeField(
        null=True,
        blank=True
    )
    
    preparation_complete_time = models.DateTimeField(
        null=True,
        blank=True
    )
    
    total_preparation_minutes = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    
    # Preparation Notes
    preparation_notes = models.TextField(blank=True)
    anticipated_challenges = models.TextField(blank=True)
    special_requirements = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('planned_session', 'facilitator')
        verbose_name = "Session Preparation Checklist"
        verbose_name_plural = "Session Preparation Checklists"
        ordering = ['-preparation_start_time']
    
    def __str__(self):
        return f"Preparation - {self.planned_session} by {self.facilitator.full_name}"
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage of checklist"""
        checkpoints = [
            self.lesson_plan_reviewed,
            self.materials_prepared,
            self.technology_tested,
            self.classroom_setup_ready,
            self.student_list_reviewed,
            self.previous_session_feedback_reviewed,
        ]
        completed = sum(checkpoints)
        return (completed / len(checkpoints)) * 100


# =========================
# STUDENT FEEDBACK - NEW
# =========================
class StudentFeedback(models.Model):
    """
    Anonymous student feedback for session quality and understanding
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    actual_session = models.ForeignKey(
        ActualSession,
        on_delete=models.CASCADE,
        related_name="student_feedback",
        help_text="Reference to the conducted session"
    )
    
    # Anonymous student identifier (not linked to specific student)
    anonymous_student_id = models.CharField(
        max_length=50,
        help_text="Anonymous identifier for student"
    )
    
    # Student Feedback Questions
    session_rating = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="Rate the session (1 = Poor, 5 = Excellent)"
    )
    
    topic_understanding = models.CharField(
        max_length=20,
        choices=[
            ('yes', 'Yes'),
            ('somewhat', 'Somewhat'),
            ('no', 'No'),
        ],
        help_text="Was the topic easy to understand?"
    )
    
    teacher_clarity = models.CharField(
        max_length=20,
        choices=[
            ('yes', 'Yes'),
            ('sometimes', 'Sometimes'),
            ('no', 'No'),
        ],
        help_text="Did the teacher explain clearly?"
    )
    
    session_highlights = models.TextField(
        help_text="What did you like most in this session?"
    )
    
    improvement_suggestions = models.TextField(
        help_text="What can be improved in the next session?"
    )
    
    additional_suggestions = models.TextField(
        blank=True,
        help_text="Do you have any suggestions? (optional)"
    )
    
    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        unique_together = ('actual_session', 'anonymous_student_id')
        ordering = ['-submitted_at']
        verbose_name = "Student Feedback"
        verbose_name_plural = "Student Feedback"
    
    def __str__(self):
        return f"Student Feedback - {self.actual_session} (Rating: {self.session_rating})"


# =========================
# TEACHER FEEDBACK - NEW
# =========================
class TeacherFeedback(models.Model):
    """
    Teacher reflection feedback for session delivery and student engagement
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    actual_session = models.ForeignKey(
        ActualSession,
        on_delete=models.CASCADE,
        related_name="teacher_feedback",
        help_text="Reference to the conducted session"
    )
    
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_feedback",
        help_text="Who provided the feedback"
    )
    
    # Teacher Reflection Questions
    class_engagement = models.CharField(
        max_length=20,
        choices=[
            ('highly', 'Highly'),
            ('moderate', 'Moderate'),
            ('low', 'Low'),
        ],
        help_text="Was the class engaged?"
    )
    
    session_completion = models.CharField(
        max_length=20,
        choices=[
            ('yes', 'Yes'),
            ('partly', 'Partly'),
            ('no', 'No'),
        ],
        help_text="Was the session completed as planned?"
    )
    
    student_struggles = models.TextField(
        help_text="Which part students struggled with most?"
    )
    
    successful_elements = models.TextField(
        help_text="What worked well in this session?"
    )
    
    improvement_areas = models.TextField(
        help_text="What should be improved for next time?"
    )
    
    resource_needs = models.TextField(
        blank=True,
        help_text="Any support/resources required? (optional)"
    )
    
    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('actual_session', 'facilitator')
        ordering = ['-submitted_at']
        verbose_name = "Teacher Feedback"
        verbose_name_plural = "Teacher Feedback"
    
    def __str__(self):
        return f"Teacher Feedback - {self.actual_session} by {self.facilitator.full_name}"


# =========================
# FEEDBACK ANALYTICS - NEW
# =========================
class FeedbackAnalytics(models.Model):
    """
    Calculated analytics and metrics for session feedback
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    actual_session = models.ForeignKey(
        ActualSession,
        on_delete=models.CASCADE,
        related_name="feedback_analytics",
        help_text="Reference to the session"
    )
    
    # Student Feedback Analytics
    average_student_rating = models.FloatField(
        null=True, 
        blank=True,
        help_text="Average session rating from students"
    )
    
    understanding_percentage = models.FloatField(
        null=True, 
        blank=True,
        help_text="Percentage of students who understood the topic"
    )
    
    clarity_percentage = models.FloatField(
        null=True, 
        blank=True,
        help_text="Percentage of students who found teacher clear"
    )
    
    student_feedback_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of student feedback responses"
    )
    
    # Teacher Feedback Analytics
    engagement_score = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Engagement level score (1-3)"
    )
    
    completion_score = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Session completion score (1-3)"
    )
    
    # Correlation and Quality Metrics
    feedback_correlation_score = models.FloatField(
        null=True, 
        blank=True,
        help_text="Correlation between student and teacher feedback"
    )
    
    session_quality_score = models.FloatField(
        null=True, 
        blank=True,
        help_text="Overall session quality score"
    )
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('actual_session',)
        verbose_name = "Feedback Analytics"
        verbose_name_plural = "Feedback Analytics"
        ordering = ['-calculated_at']
    
    def __str__(self):
        return f"Analytics - {self.actual_session}"
    
    def calculate_analytics(self):
        """Calculate analytics from feedback data"""
        # Get student feedback
        student_feedback = self.actual_session.student_feedback.all()
        
        if student_feedback.exists():
            # Calculate student metrics
            ratings = [f.session_rating for f in student_feedback]
            self.average_student_rating = sum(ratings) / len(ratings)
            
            understanding_yes = student_feedback.filter(topic_understanding='yes').count()
            self.understanding_percentage = (understanding_yes / student_feedback.count()) * 100
            
            clarity_yes = student_feedback.filter(teacher_clarity='yes').count()
            self.clarity_percentage = (clarity_yes / student_feedback.count()) * 100
            
            self.student_feedback_count = student_feedback.count()
        
        # Get teacher feedback
        teacher_feedback = self.actual_session.teacher_feedback.first()
        if teacher_feedback:
            # Convert engagement to score
            engagement_map = {'highly': 3, 'moderate': 2, 'low': 1}
            self.engagement_score = engagement_map.get(teacher_feedback.class_engagement, 0)
            
            # Convert completion to score
            completion_map = {'yes': 3, 'partly': 2, 'no': 1}
            self.completion_score = completion_map.get(teacher_feedback.session_completion, 0)
        
        # Calculate overall quality score
        if self.average_student_rating and self.engagement_score:
            self.session_quality_score = (
                (self.average_student_rating / 5) * 0.6 +
                (self.engagement_score / 3) * 0.4
            ) * 100
        
        self.save()
