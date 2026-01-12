# CLAS Platform - Complete Database Design

## All Models & Fields

### 1. Role Model
```python
class Role(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    
    class Meta:
        db_table = 'role'
    
    # Fixed role IDs (prevents role mismatch bugs):
    # 0 = Admin
    # 1 = Supervisor
    # 2 = Facilitator
```

### 2. User Model (Custom)
```python
class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    supervisor = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'user'
```

### 3. School Model
```python
class School(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    udise = models.CharField(max_length=50, unique=True)
    block = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    area = models.CharField(max_length=100)
    address = models.TextField()
    contact_person = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    status = models.SmallIntegerField(choices=[(1, 'Active'), (0, 'Inactive')], default=1)
    enrolled_students = models.PositiveIntegerField(default=0)
    avg_attendance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    validation_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    profile_image = models.ImageField(upload_to='schools/', null=True, blank=True)
    logo = models.ImageField(upload_to='schools/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'school'
```

### 4. ClassSection Model
```python
class ClassSection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    class_level = models.CharField(max_length=10)
    section = models.CharField(max_length=10)
    academic_year = models.CharField(max_length=20)
    display_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'class_section'
        unique_together = ('school', 'class_level', 'section', 'academic_year')
```

### 5. Student Model
```python
class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    enrollment_number = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=255)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'student'
```

### 6. Enrollment Model
```python
class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE)
    start_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'enrollment'
        unique_together = ('student', 'class_section', 'is_active')
        indexes = [
            models.Index(fields=['student', 'is_active']),
            models.Index(fields=['school', 'is_active']),
        ]
```

### 7. FacilitatorSchool Model
```python
class FacilitatorSchool(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    facilitator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_schools')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='facilitators')
    assigned_date = models.DateField(auto_now_add=True)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'facilitator_school'
        unique_together = ('facilitator', 'school')
```

### 8. PlannedSession Model
```python
class PlannedSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE)
    day_number = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    sequence_position = models.PositiveIntegerField()
    is_required = models.BooleanField(default=True)
    prerequisite_days = models.JSONField(default=list)
    grouped_session_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'planned_session'
        unique_together = ('class_section', 'day_number')
```

### 9. SessionStep Model
```python
class SessionStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    planned_session = models.ForeignKey(PlannedSession, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    subject = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    description = models.TextField()
    youtube_url = models.URLField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField()
    
    class Meta:
        db_table = 'session_step'
        unique_together = ('planned_session', 'order')
```

### 10. ActualSession Model
```python
class ActualSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    planned_session = models.ForeignKey(PlannedSession, on_delete=models.CASCADE)
    date = models.DateField()
    facilitator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.SmallIntegerField(choices=SessionStatus.choices)
    remarks = models.TextField(blank=True)
    conducted_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    attendance_marked = models.BooleanField(default=False)
    status_changed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='status_changes')
    status_change_reason = models.TextField(blank=True)
    can_be_rescheduled = models.BooleanField(default=True)
    cancellation_reason = models.CharField(max_length=255, blank=True)
    cancellation_category = models.CharField(max_length=50, blank=True)
    is_permanent_cancellation = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'actual_session'
        unique_together = ('planned_session', 'date')
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['facilitator', 'date']),
            models.Index(fields=['status', 'date']),
        ]
        # NOTE: v2 Plan - Split into ActualSession + SessionCancellation (OneToOne)
```

### 11. Attendance Model
```python
class Attendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    actual_session = models.ForeignKey(ActualSession, on_delete=models.CASCADE)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE)
    status = models.SmallIntegerField(choices=AttendanceStatus.choices)
    marked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'attendance'
        unique_together = ('actual_session', 'enrollment')
        indexes = [
            models.Index(fields=['actual_session']),
            models.Index(fields=['enrollment']),
            models.Index(fields=['status', 'marked_at']),
        ]
```

### 12. CurriculumSession Model
```python
class CurriculumSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    day_number = models.PositiveIntegerField()
    language = models.CharField(max_length=20)
    content = models.TextField()
    learning_objectives = models.TextField()
    activities = models.JSONField(default=list)
    resources = models.JSONField(default=list)
    template = models.ForeignKey('SessionTemplate', on_delete=models.SET_NULL, null=True)
    status = models.SmallIntegerField(choices=CurriculumStatus.choices)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    usage_count = models.PositiveIntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    is_active_for_facilitators = models.BooleanField(default=True)
    fallback_to_static = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'curriculum_session'
        unique_together = ('day_number', 'language')
```

### 13. SessionTemplate Model
```python
class SessionTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField()
    language = models.CharField(max_length=20)
    content_structure = models.JSONField()
    default_activities = models.JSONField()
    learning_objectives = models.TextField()
    usage_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'session_template'
```

### 14. SessionUsageLog Model
```python
class SessionUsageLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    session = models.ForeignKey(CurriculumSession, on_delete=models.CASCADE)
    facilitator = models.ForeignKey(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    access_timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.PositiveIntegerField()
    actions = models.JSONField(default=list)
    
    class Meta:
        db_table = 'session_usage_log'
```

### 15. CurriculumUsageLog Model
```python
class CurriculumUsageLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    curriculum_session = models.ForeignKey(CurriculumSession, on_delete=models.CASCADE)
    facilitator = models.ForeignKey(User, on_delete=models.CASCADE)
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE)
    planned_session = models.ForeignKey(PlannedSession, on_delete=models.CASCADE)
    access_timestamp = models.DateTimeField(auto_now_add=True)
    session_duration = models.PositiveIntegerField()
    content_source = models.CharField(max_length=50)
    user_agent = models.TextField()
    ip_address = models.GenericIPAddressField()
    
    class Meta:
        db_table = 'curriculum_usage_log'
```

### 16. SessionContentMapping Model
```python
class SessionContentMapping(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    planned_session = models.OneToOneField(PlannedSession, on_delete=models.CASCADE)
    curriculum_session = models.ForeignKey(CurriculumSession, on_delete=models.CASCADE)
    content_source = models.CharField(max_length=50)
    last_sync = models.DateTimeField(auto_now=True)
    sync_status = models.CharField(max_length=20)
    
    class Meta:
        db_table = 'session_content_mapping'
```

### 17. LessonPlanUpload Model
```python
class LessonPlanUpload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    planned_session = models.ForeignKey(PlannedSession, on_delete=models.CASCADE)
    facilitator = models.ForeignKey(User, on_delete=models.CASCADE)
    upload_date = models.DateField(auto_now_add=True)
    lesson_plan_file = models.FileField(upload_to='lesson_plans/')
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    upload_notes = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_plans')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'lesson_plan_upload'
        unique_together = ('planned_session', 'facilitator')
```

### 18. SessionReward Model
```python
class SessionReward(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    actual_session = models.ForeignKey(ActualSession, on_delete=models.CASCADE)
    facilitator = models.ForeignKey(User, on_delete=models.CASCADE)
    reward_type = models.CharField(max_length=50)
    reward_photo = models.ImageField(upload_to='rewards/', null=True, blank=True)
    reward_description = models.TextField()
    student_names = models.TextField()
    reward_date = models.DateTimeField(auto_now_add=True)
    is_visible_to_admin = models.BooleanField(default=True)
    admin_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'session_reward'
```

### 19. SessionPreparationChecklist Model
```python
class SessionPreparationChecklist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    planned_session = models.ForeignKey(PlannedSession, on_delete=models.CASCADE)
    facilitator = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson_plan_reviewed = models.BooleanField(default=False)
    materials_prepared = models.BooleanField(default=False)
    technology_tested = models.BooleanField(default=False)
    classroom_setup_ready = models.BooleanField(default=False)
    student_list_reviewed = models.BooleanField(default=False)
    previous_session_feedback_reviewed = models.BooleanField(default=False)
    checkpoints_completed_at = models.JSONField(default=dict)
    preparation_start_time = models.DateTimeField(null=True, blank=True)
    preparation_complete_time = models.DateTimeField(null=True, blank=True)
    total_preparation_minutes = models.PositiveIntegerField(default=0)
    preparation_notes = models.TextField(blank=True)
    anticipated_challenges = models.TextField(blank=True)
    special_requirements = models.TextField(blank=True)
    
    class Meta:
        db_table = 'session_preparation_checklist'
        unique_together = ('planned_session', 'facilitator')
```

### 20. FacilitatorTask Model
```python
class FacilitatorTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    actual_session = models.ForeignKey(ActualSession, on_delete=models.CASCADE)
    facilitator = models.ForeignKey(User, on_delete=models.CASCADE)
    media_type = models.CharField(max_length=50)
    media_file = models.FileField(upload_to='tasks/', null=True, blank=True)
    facebook_link = models.URLField(null=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'facilitator_task'
```

### 21. SessionFeedback Model
```python
class SessionFeedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    actual_session = models.ForeignKey(ActualSession, on_delete=models.CASCADE)
    facilitator = models.ForeignKey(User, on_delete=models.CASCADE)
    student_engagement_level = models.PositiveIntegerField()
    student_understanding_level = models.PositiveIntegerField()
    student_participation_notes = models.TextField()
    learning_objectives_met = models.BooleanField()
    challenging_topics = models.TextField()
    student_questions = models.TextField()
    session_completion_percentage = models.PositiveIntegerField()
    time_management_rating = models.PositiveIntegerField()
    content_difficulty_rating = models.PositiveIntegerField()
    facilitator_satisfaction = models.PositiveIntegerField()
    what_went_well = models.TextField()
    areas_for_improvement = models.TextField()
    next_session_preparation = models.TextField()
    additional_notes = models.TextField()
    feedback_date = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'session_feedback'
        unique_together = ('actual_session', 'facilitator')
```

### 22. StudentFeedback Model
```python
class StudentFeedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    actual_session = models.ForeignKey(ActualSession, on_delete=models.CASCADE)
    anonymous_student_id = models.CharField(max_length=50)
    session_rating = models.PositiveIntegerField()
    topic_understanding = models.CharField(max_length=50)
    teacher_clarity = models.CharField(max_length=50)
    session_highlights = models.TextField()
    improvement_suggestions = models.TextField()
    additional_suggestions = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    
    class Meta:
        db_table = 'student_feedback'
        unique_together = ('actual_session', 'anonymous_student_id')
```

### 23. TeacherFeedback Model
```python
class TeacherFeedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    actual_session = models.ForeignKey(ActualSession, on_delete=models.CASCADE)
    facilitator = models.ForeignKey(User, on_delete=models.CASCADE)
    class_engagement = models.CharField(max_length=50)
    session_completion = models.CharField(max_length=50)
    student_struggles = models.TextField()
    successful_elements = models.TextField()
    improvement_areas = models.TextField()
    resource_needs = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'teacher_feedback'
        unique_together = ('actual_session', 'facilitator')
```

### 24. FeedbackAnalytics Model
```python
class FeedbackAnalytics(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    actual_session = models.OneToOneField(ActualSession, on_delete=models.CASCADE)
    average_student_rating = models.FloatField()
    understanding_percentage = models.FloatField()
    clarity_percentage = models.FloatField()
    student_feedback_count = models.PositiveIntegerField()
    engagement_score = models.PositiveIntegerField()
    completion_score = models.PositiveIntegerField()
    feedback_correlation_score = models.FloatField()
    session_quality_score = models.FloatField()
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feedback_analytics'
```

### 25. Subject Model
```python
class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'subject'
```

### 26. PerformanceCutoff Model
```python
class PerformanceCutoff(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    class_section = models.OneToOneField(ClassSection, on_delete=models.CASCADE)
    passing_score = models.IntegerField(default=40)
    excellent_score = models.IntegerField(default=80)
    good_score = models.IntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'performance_cutoff'
```

### 27. StudentPerformance Model
```python
class StudentPerformance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    score = models.IntegerField()
    grade = models.CharField(max_length=1)
    remarks = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_performance'
        unique_together = ('student', 'class_section', 'subject')
```

### 28. StudentPerformanceSummary Model
```python
class StudentPerformanceSummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE)
    average_score = models.FloatField()
    total_subjects = models.IntegerField()
    passed_subjects = models.IntegerField()
    failed_subjects = models.IntegerField()
    rank = models.IntegerField(null=True, blank=True)
    is_passed = models.BooleanField()
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_performance_summary'
        unique_together = ('student', 'class_section')
```

### 29. SupervisorCalendar Model
```python
class SupervisorCalendar(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    supervisor = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'supervisor_calendar'
```

### 30. CalendarDate Model
```python
class CalendarDate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    calendar = models.ForeignKey(SupervisorCalendar, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    date_type = models.SmallIntegerField(choices=DateType.choices)
    class_sections = models.ManyToManyField(ClassSection, blank=True)
    class_section = models.ForeignKey(ClassSection, null=True, blank=True, on_delete=models.SET_NULL)  # LEGACY - to be removed in v2
    school = models.ForeignKey(School, null=True, blank=True, on_delete=models.CASCADE)
    holiday_name = models.CharField(max_length=255, blank=True)
    office_task_description = models.TextField(blank=True)
    assigned_facilitators = models.ManyToManyField(User, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'calendar_date'
        # NOTE: class_section FK is legacy (backward compatibility)
        # Use class_sections M2M for new code
```

### 31. OfficeWorkAttendance Model
```python
class OfficeWorkAttendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    calendar_date = models.ForeignKey(CalendarDate, on_delete=models.CASCADE)
    facilitator = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20)
    remarks = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'office_work_attendance'
        unique_together = ('calendar_date', 'facilitator')
```

---

## Enum Choices

### SessionStatus
```python
class SessionStatus(models.IntegerChoices):
    CONDUCTED = 1, "Conducted"
    HOLIDAY = 2, "Holiday"
    CANCELLED = 3, "Cancelled"
```

### AttendanceStatus
```python
class AttendanceStatus(models.IntegerChoices):
    PRESENT = 1, "Present"
    ABSENT = 2, "Absent"
    LEAVE = 3, "Leave"
```

### DateType
```python
class DateType(models.IntegerChoices):
    SESSION = 1, "Planned Session"
    HOLIDAY = 2, "Holiday / No Session"
    OFFICE_WORK = 3, "Office Work / Task"
```

### CurriculumStatus
```python
class CurriculumStatus(models.IntegerChoices):
    DRAFT = 1, "Draft"
    PUBLISHED = 2, "Published"
    ARCHIVED = 3, "Archived"
```

---

## Summary

- **Total Models**: 31
- **Total Fields**: 300+
- **Relationships**: 50+
- **Unique Constraints**: 15+
- **Indexes**: 20+

---

## ✅ Required Fixes Applied

### 1. Role Model - Fixed ID Type ✅
- **Changed**: SmallAutoField → PositiveSmallIntegerField
- **Reason**: Prevents role ID mismatch across environments
- **Fixed IDs**: 0=Admin, 1=Supervisor, 2=Facilitator

### 2. Critical Indexes Added ✅
- **Attendance**: actual_session, enrollment, status+marked_at
- **ActualSession**: date, facilitator+date, status+date
- **Enrollment**: student+is_active, school+is_active
- **Reason**: Critical for reports and query performance

### 3. CalendarDate Legacy FK Documented ✅
- **Note**: class_section FK is legacy (backward compatibility)
- **Use**: class_sections M2M for new code
- **Plan**: Remove in v2

### 4. ActualSession Heavy Table Noted ✅
- **Current**: OK for v1 (cancellation fields included)
- **v2 Plan**: Split into ActualSession + SessionCancellation (OneToOne)
- **No action needed now**

---

## 🔮 Future Optimizations (v2 Plan)

### Optional Improvements (Not Required Now)

| Area | Suggestion | Priority |
|------|-----------|----------|
| JSONField | Move prerequisite_days to relation | Low |
| OfficeWorkAttendance.status | Convert to IntegerChoices | Low |
| Subject | Add unique constraint on name | Low |
| Student | Add index on enrollment_number | Medium |
| Logs | Use BigAutoField instead of UUID | Low |
| ActualSession | Split into ActualSession + SessionCancellation | Medium |

### Performance Optimizations (v2)

1. **Log Tables**: Convert UUID to BigAutoField
   - Reason: Logs grow fast, UUID hurts index size
   - Impact: Faster queries on large datasets

2. **ActualSession Split**: Create SessionCancellation table
   - Reason: Reduce row size for common queries
   - Impact: Faster session queries

3. **JSONField Refactoring**: Move to relations
   - Reason: Better queryability
   - Impact: Easier filtering and reporting

---

## 🔒 Data Integrity Notes

- ✅ All foreign keys have proper cascade/set_null behavior
- ✅ Unique constraints prevent duplicates
- ✅ Indexes optimize query performance
- ✅ Role IDs are fixed (no environment mismatch)
- ✅ Legacy fields documented for backward compatibility

---

## 📋 Migration Checklist

When deploying this schema:

- [ ] Create all 31 models
- [ ] Run migrations: `python manage.py migrate`
- [ ] Seed Role table with fixed IDs (0, 1, 2)
- [ ] Verify all indexes are created
- [ ] Test access control with fixed role IDs
- [ ] Verify backward compatibility with legacy fields
- [ ] Run full test suite

---

## 🚀 Production Ready

This database design is:
- ✅ Normalized and optimized
- ✅ Indexed for performance
- ✅ Documented for maintenance
- ✅ Backward compatible
- ✅ Ready for deployment



