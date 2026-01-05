import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class CurriculumSession(models.Model):
    """
    Represents a curriculum session for admin management.
    Language-specific and day-based for the entire curriculum (not class-specific).
    """
    
    LANGUAGE_CHOICES = [
        ('hindi', 'Hindi'),
        ('english', 'English'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    title = models.CharField(
        max_length=255,
        help_text="Session title/name"
    )
    
    day_number = models.PositiveIntegerField(
        help_text="Day in curriculum sequence (1-150)"
    )
    
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        help_text="Session language (Hindi/English)"
    )
    
    content = models.TextField(
        blank=True,
        help_text="Rich text session content"
    )
    
    learning_objectives = models.TextField(
        blank=True,
        help_text="Session learning goals"
    )
    
    activities = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured activity data"
    )
    
    resources = models.JSONField(
        default=dict,
        blank=True,
        help_text="Links to videos, documents, media"
    )
    
    template = models.ForeignKey(
        'SessionTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
        help_text="Optional source template"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_sessions',
        help_text="Administrator who created session"
    )
    
    # New integration fields
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times accessed by facilitators"
    )
    
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time content was accessed by a facilitator"
    )
    
    is_active_for_facilitators = models.BooleanField(
        default=True,
        help_text="Whether facilitators should see this content"
    )
    
    fallback_to_static = models.BooleanField(
        default=False,
        help_text="Force fallback to static content for this day/language"
    )

    class Meta:
        ordering = ['language', 'day_number']
        unique_together = ('day_number', 'language')
        verbose_name = "Curriculum Session"
        verbose_name_plural = "Curriculum Sessions"

    def clean(self):
        if self.day_number < 1 or self.day_number > 150:
            raise ValidationError("Day number must be between 1 and 150")

    def __str__(self):
        return f"{self.get_language_display()} - Day {self.day_number}: {self.title}"


class SessionTemplate(models.Model):
    """
    Represents reusable templates for creating standardized sessions.
    """
    
    LANGUAGE_CHOICES = [
        ('hindi', 'Hindi'),
        ('english', 'English'),
        ('both', 'Both'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(
        max_length=255,
        help_text="Template name"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Template description"
    )
    
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='both',
        help_text="Target language (Hindi/English/Both)"
    )
    
    content_structure = models.JSONField(
        default=dict,
        blank=True,
        help_text="Template content structure"
    )
    
    default_activities = models.JSONField(
        default=dict,
        blank=True,
        help_text="Standard activities for this template"
    )
    
    learning_objectives = models.TextField(
        blank=True,
        help_text="Default learning objectives"
    )
    
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of sessions using this template"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Session Template"
        verbose_name_plural = "Session Templates"

    def __str__(self):
        return f"{self.name} ({self.get_language_display()})"


class SessionUsageLog(models.Model):
    """
    Tracks facilitator access to sessions for analytics and reporting.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    session = models.ForeignKey(
        CurriculumSession,
        on_delete=models.CASCADE,
        related_name='session_usage_logs',
        help_text="Reference to accessed session"
    )
    
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='session_accesses',
        help_text="Facilitator who accessed session"
    )
    
    school = models.ForeignKey(
        'School',
        on_delete=models.CASCADE,
        related_name='session_accesses',
        help_text="School context of access"
    )
    
    access_timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When session was accessed"
    )
    
    duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time spent viewing session (seconds)"
    )
    
    actions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Actions taken during session view"
    )

    class Meta:
        ordering = ['-access_timestamp']
        verbose_name = "Session Usage Log"
        verbose_name_plural = "Session Usage Logs"

    def __str__(self):
        return f"{self.facilitator} accessed {self.session} at {self.access_timestamp}"


class ImportHistory(models.Model):
    """
    Records session import operations for audit and rollback purposes.
    """
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('partial', 'Partial'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    import_file = models.FileField(
        upload_to='session_imports/',
        help_text="Original import file"
    )
    
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='import_operations',
        help_text="Administrator who performed import"
    )
    
    import_timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When import was performed"
    )
    
    sessions_created = models.PositiveIntegerField(
        default=0,
        help_text="Number of new sessions created"
    )
    
    sessions_updated = models.PositiveIntegerField(
        default=0,
        help_text="Number of existing sessions updated"
    )
    
    errors = models.JSONField(
        default=list,
        blank=True,
        help_text="Import errors and warnings"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='success'
    )

    class Meta:
        ordering = ['-import_timestamp']
        verbose_name = "Import History"
        verbose_name_plural = "Import Histories"

    def __str__(self):
        return f"Import by {self.imported_by} on {self.import_timestamp} - {self.status}"


class SessionVersionHistory(models.Model):
    """
    Maintains version history for sessions for audit and rollback purposes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    session = models.ForeignKey(
        CurriculumSession,
        on_delete=models.CASCADE,
        related_name='version_history'
    )
    
    version_number = models.PositiveIntegerField()
    
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    learning_objectives = models.TextField(blank=True)
    activities = models.JSONField(default=dict, blank=True)
    resources = models.JSONField(default=dict, blank=True)
    
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who made this version"
    )
    
    modified_at = models.DateTimeField(auto_now_add=True)
    
    change_summary = models.TextField(
        blank=True,
        help_text="Summary of changes made in this version"
    )

    class Meta:
        ordering = ['-version_number']
        unique_together = ('session', 'version_number')
        verbose_name = "Session Version History"
        verbose_name_plural = "Session Version Histories"

    def __str__(self):
        return f"{self.session} - Version {self.version_number}"


class CurriculumUsageLog(models.Model):
    """
    Tracks facilitator access to curriculum content for analytics.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    curriculum_session = models.ForeignKey(
        CurriculumSession,
        on_delete=models.CASCADE,
        related_name='curriculum_usage_logs'
    )
    
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='curriculum_accesses'
    )
    
    class_section = models.ForeignKey(
        'ClassSection',
        on_delete=models.CASCADE,
        related_name='curriculum_accesses'
    )
    
    planned_session = models.ForeignKey(
        'PlannedSession',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Associated PlannedSession if applicable"
    )
    
    access_timestamp = models.DateTimeField(auto_now_add=True)
    session_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time spent viewing content in seconds"
    )
    
    content_source = models.CharField(
        max_length=20,
        choices=[
            ('admin_managed', 'Admin Managed'),
            ('static_fallback', 'Static Fallback'),
        ],
        help_text="Source of the curriculum content"
    )
    
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-access_timestamp']
        verbose_name = "Curriculum Usage Log"
        verbose_name_plural = "Curriculum Usage Logs"

    def __str__(self):
        return f"{self.facilitator} accessed {self.curriculum_session} at {self.access_timestamp}"


class SessionContentMapping(models.Model):
    """
    Links PlannedSessions with their corresponding CurriculumSessions.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    planned_session = models.OneToOneField(
        'PlannedSession',
        on_delete=models.CASCADE,
        related_name='curriculum_mapping'
    )
    
    curriculum_session = models.ForeignKey(
        CurriculumSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='planned_mappings'
    )
    
    content_source = models.CharField(
        max_length=20,
        choices=[
            ('admin_managed', 'Admin Managed'),
            ('static_fallback', 'Static Fallback'),
            ('not_available', 'Not Available'),
        ],
        default='static_fallback'
    )
    
    last_sync = models.DateTimeField(auto_now=True)
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('synced', 'Synced'),
            ('outdated', 'Outdated'),
            ('failed', 'Failed'),
        ],
        default='synced'
    )

    class Meta:
        verbose_name = "Session Content Mapping"
        verbose_name_plural = "Session Content Mappings"

    def __str__(self):
        return f"{self.planned_session} -> {self.curriculum_session or 'Static Content'}"