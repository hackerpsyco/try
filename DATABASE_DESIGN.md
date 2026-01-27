# CLAS Platform - Complete Database Design & Architecture

**Last Updated**: January 26, 2026  
**Total Models**: 35  
**Total Fields**: 350+  
**Relationships**: 60+  
**Indexes**: 25+

---

## 📋 Table of Contents

1. [Core User & Organization Models](#core-user--organization-models)
2. [School & Class Management](#school--class-management)
3. [Student & Enrollment](#student--enrollment)
4. [Session Management](#session-management)
5. [Curriculum & Content](#curriculum--content)
6. [Feedback & Analytics](#feedback--analytics)
7. [Performance Tracking](#performance-tracking)
8. [Calendar & Scheduling](#calendar--scheduling)
9. [Enum Choices](#enum-choices)
10. [Data Relationships Diagram](#data-relationships-diagram)
11. [Connection Logic](#connection-logic)
12. [Indexes & Performance](#indexes--performance)

---

## Core User & Organization Models

### 1. Role Model
**File**: `class/models/users.py`

```python
class Role(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    
    # Fixed role IDs:
    # 0 = Admin
    # 1 = Supervisor
    # 2 = Facilitator
```

**Purpose**: Defines user roles in the system  
**Key Fields**: id (fixed), name (unique)  
**Relationships**: Referenced by User model

---

### 2. User Model (Custom)
**File**: `class/models/users.py`

```python
class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    
    # Supervisor → Facilitator mapping
    supervisor = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='facilitators',
        limit_choices_to={'role__id': 1}  # Only supervisors
    )
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
```

**Purpose**: Custom user model with role-based access control  
**Key Features**:
- UUID primary key for security
- Self-referential FK for supervisor-facilitator hierarchy
- Django permissions support
- Audit timestamps

**Relationships**:
- `role` → Role (PROTECT - cannot delete role if users exist)
- `supervisor` → User (self-referential, only role_id=1)
- Related: `facilitators` (reverse from supervisor)

---

## School & Class Management

### 3. Cluster Model
**File**: `class/models/cluster.py`

```python
class Cluster(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default="Madhya Pradesh")
    description = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Purpose**: Geographic/administrative grouping of schools  
**Key Fields**: name (unique), district, state, coordinates  
**Relationships**: Referenced by School model

---

### 4. School Model
**File**: `class/models/school.py`

```python
class School(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    udise = models.CharField(max_length=50, unique=True)
    block = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default="Madhya Pradesh")
    
    cluster = models.ForeignKey(
        'Cluster',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='schools'
    )
    
    area = models.CharField(max_length=200, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Location coordinates
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=28.7041)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=77.1025)
    
    status = models.SmallIntegerField(
        choices=[(1, 'Active'), (0, 'Inactive')],
        default=1
    )
    
    # Cached dashboard fields
    enrolled_students = models.PositiveIntegerField(default=0)
    avg_attendance_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    validation_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    profile_image = models.ImageField(upload_to='schools/', null=True, blank=True)
    logo = models.ImageField(upload_to='schools/logos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Purpose**: School entity with location and contact information  
**Key Fields**: udise (unique), cluster, coordinates, status  
**Relationships**:
- `cluster` → Cluster (SET_NULL)
- Related: `class_sections`, `enrollments`, `facilitators`, `calendar_entries`

---

### 5. ClassSection Model
**File**: `class/models/class_section.py`

```python
class ClassSection(models.Model):
    CLASS_LEVEL_ORDER = {
        'LKG': 1, 'UKG': 2, '1': 3, '2': 4, '3': 5, '4': 6, '5': 7,
        '6': 8, '7': 9, '8': 10, '9': 11, '10': 12
    }
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='class_sections'
    )
    
    class_level = models.CharField(max_length=8)  # LKG, UKG, 1, 2, etc.
    section = models.CharField(max_length=8, blank=True, null=True)  # A, B
    academic_year = models.CharField(max_length=9, default="2024-2025")
    display_name = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('school', 'class_level', 'section', 'academic_year')
```

**Purpose**: Represents a class section within a school  
**Key Fields**: class_level, section, academic_year  
**Unique Constraint**: (school, class_level, section, academic_year)  
**Relationships**:
- `school` → School (CASCADE)
- Related: `enrollments`, `planned_sessions`, `calendar_sessions`

---

### 6. FacilitatorSchool Model
**File**: `class/models/facilitor_school.py`

```python
class FacilitatorSchool(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    facilitator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_schools',
        limit_choices_to={'role_id': 2}  # Only facilitators
    )
    
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='facilitators'
    )
    
    assigned_date = models.DateField(auto_now_add=True)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('facilitator', 'school')
        indexes = [
            models.Index(fields=['is_active', 'school'], name='facsch_active_sch_idx'),
            models.Index(fields=['facilitator', 'is_active'], name='facsch_facil_active_idx'),
        ]
```

**Purpose**: Maps facilitators to schools (many-to-many with metadata)  
**Key Fields**: is_primary, is_active, assigned_date  
**Unique Constraint**: (facilitator, school)  
**Relationships**:
- `facilitator` → User (CASCADE, role_id=2)
- `school` → School (CASCADE)

---

## Student & Enrollment

### 7. Student Model
**File**: `class/models/students.py`

```python
class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment_number = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[('M', 'Male'), ('F', 'Female')]
    )
    created_at = models.DateTimeField(auto_now_add=True)
```

**Purpose**: Student entity  
**Key Fields**: enrollment_number (unique), full_name, dob, gender  
**Relationships**: Related: `enrollments`, `performance_records`

---

### 8. Enrollment Model
**File**: `class/models/students.py`

```python
class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    
    school = models.ForeignKey(
        'class.School',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    
    class_section = models.ForeignKey(
        'class.ClassSection',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    
    start_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('student', 'class_section', 'is_active')
        indexes = [
            models.Index(fields=['is_active', 'school'], name='enroll_active_sch_idx'),
            models.Index(fields=['student', 'is_active'], name='enroll_stud_active_idx'),
        ]
```

**Purpose**: Links students to class sections  
**Key Fields**: start_date, is_active  
**Unique Constraint**: (student, class_section, is_active)  
**Relationships**:
- `student` → Student (CASCADE)
- `school` → School (CASCADE)
- `class_section` → ClassSection (CASCADE)
- Related: `attendances`

---

## Session Management

### 9. PlannedSession Model
**File**: `class/models/students.py`

```python
class PlannedSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class_section = models.ForeignKey(
        'class.ClassSection',
        on_delete=models.CASCADE,
        related_name='planned_sessions'
    )
    
    day_number = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Sequence management
    sequence_position = models.PositiveIntegerField(null=True, blank=True)
    is_required = models.BooleanField(default=True)
    prerequisite_days = models.JSONField(default=list, blank=True)
    
    # Grouped session support
    grouped_session_id = models.UUIDField(null=True, blank=True)
    
    # Content versioning
    curriculum_session = models.ForeignKey(
        'CurriculumSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='planned_sessions'
    )
    
    content_version = models.PositiveIntegerField(default=1)
    last_content_sync = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('class_section', 'day_number')
        indexes = [
            models.Index(fields=['class_section', 'day_number']),
            models.Index(fields=['class_section', 'is_active']),
        ]
```

**Purpose**: Represents a logical teaching day (Day 1, Day 2, etc.)  
**Key Fields**: day_number, sequence_position, grouped_session_id  
**Unique Constraint**: (class_section, day_number)  
**Relationships**:
- `class_section` → ClassSection (CASCADE)
- `curriculum_session` → CurriculumSession (SET_NULL)
- Related: `steps`, `actual_sessions`, `lesson_plan_uploads`, `preparation_checklists`

---

### 10. SessionStep Model
**File**: `class/models/students.py`

```python
class SessionStep(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    planned_session = models.ForeignKey(
        PlannedSession,
        on_delete=models.CASCADE,
        related_name='steps'
    )
    
    order = models.PositiveIntegerField()
    subject = models.CharField(
        max_length=30,
        choices=[
            ('english', 'English'),
            ('hindi', 'Hindi'),
            ('maths', 'Maths'),
            ('computer', 'Computer'),
            ('activity', 'Activity / Energizer'),
            ('mindfulness', 'Mindfulness'),
        ]
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    youtube_url = models.URLField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ('planned_session', 'order')
```

**Purpose**: Represents activities/steps within a planned session  
**Key Fields**: order, subject, title, duration_minutes  
**Unique Constraint**: (planned_session, order)  
**Relationships**: `planned_session` → PlannedSession (CASCADE)

---

### 11. ActualSession Model
**File**: `class/models/students.py`

```python
class ActualSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    planned_session = models.ForeignKey(
        PlannedSession,
        on_delete=models.CASCADE,
        related_name='actual_sessions'
    )
    
    date = models.DateField()
    
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_sessions'
    )
    
    status = models.SmallIntegerField(
        choices=SessionStatus.choices,
        default=SessionStatus.CONDUCTED
    )
    
    remarks = models.TextField(blank=True)
    conducted_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    attendance_marked = models.BooleanField(default=False)
    
    facilitator_attendance = models.CharField(
        max_length=10,
        choices=[('present', 'Present'), ('absent', 'Absent'), ('leave', 'Leave'), ('', 'Not Marked')],
        default='',
        blank=True
    )
    
    status_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='status_changes'
    )
    
    status_change_reason = models.TextField(blank=True)
    can_be_rescheduled = models.BooleanField(default=True)
    
    # Cancellation tracking
    cancellation_reason = models.CharField(
        max_length=50,
        choices=CANCELLATION_REASONS,
        blank=True,
        null=True
    )
    
    cancellation_category = models.CharField(max_length=50, blank=True)
    is_permanent_cancellation = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('planned_session', 'date')
        indexes = [
            models.Index(fields=['planned_session', 'status'], name='asess_sess_stat_idx'),
            models.Index(fields=['date', 'status'], name='asess_date_stat_idx'),
            models.Index(fields=['facilitator', 'date'], name='asess_facil_date_idx'),
            models.Index(fields=['status', 'date'], name='asess_stat_date_idx'),
        ]
```

**Purpose**: Represents actual execution of a planned session on a calendar date  
**Key Fields**: date, status, facilitator, attendance_marked  
**Unique Constraint**: (planned_session, date)  
**Relationships**:
- `planned_session` → PlannedSession (CASCADE)
- `facilitator` → User (SET_NULL)
- `status_changed_by` → User (SET_NULL)
- Related: `attendances`, `feedback`, `rewards`, `facilitator_tasks`

---

### 12. SessionCancellation Model
**File**: `class/models/students.py`

```python
class SessionCancellation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    actual_session = models.OneToOneField(
        ActualSession,
        on_delete=models.CASCADE,
        related_name='cancellation'
    )
    
    reason = models.CharField(
        max_length=50,
        choices=CANCELLATION_REASONS
    )
    
    category = models.CharField(max_length=50, blank=True)
    is_permanent = models.BooleanField(default=False)
    can_be_rescheduled = models.BooleanField(default=True)
    
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='session_cancellations'
    )
    
    change_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['actual_session', 'is_permanent'], name='scancel_sess_perm_idx'),
        ]
```

**Purpose**: Stores detailed cancellation information (Phase 2 optimization)  
**Key Fields**: reason, is_permanent, can_be_rescheduled  
**Relationships**: `actual_session` → ActualSession (CASCADE, OneToOne)

---

### 13. Attendance Model
**File**: `class/models/students.py`

```python
class Attendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    actual_session = models.ForeignKey(
        ActualSession,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    
    # Denormalized fields for faster reports
    student_id = models.UUIDField(db_index=True, null=True, blank=True)
    class_section_id = models.UUIDField(db_index=True, null=True, blank=True)
    school_id = models.UUIDField(db_index=True, null=True, blank=True)
    
    status = models.SmallIntegerField(
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT
    )
    
    marked_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('actual_session', 'enrollment')
        indexes = [
            models.Index(fields=['status', 'marked_at'], name='attend_status_date_idx'),
            models.Index(fields=['student_id', 'marked_at'], name='attend_stud_date_idx'),
            models.Index(fields=['class_section_id', 'marked_at'], name='attend_cls_date_idx'),
            models.Index(fields=['school_id', 'marked_at'], name='attend_sch_date_idx'),
        ]
```

**Purpose**: Tracks student attendance for each session  
**Key Fields**: status, marked_at  
**Unique Constraint**: (actual_session, enrollment)  
**Denormalized Fields**: student_id, class_section_id, school_id (for report performance)  
**Relationships**:
- `actual_session` → ActualSession (CASCADE)
- `enrollment` → Enrollment (CASCADE)

