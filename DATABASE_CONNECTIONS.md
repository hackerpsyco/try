# CLAS Platform - Database Connections & Logic

## Complete Model Relationships Map

### User Hierarchy
```
Role (0=Admin, 1=Supervisor, 2=Facilitator)
  ↓
User (email, full_name, role)
  ├─ supervisor (self-referential, only role_id=1)
  └─ facilitators (reverse from supervisor)
```

### School Organization
```
Cluster (geographic grouping)
  ↓
School (name, udise, district, state, coordinates)
  ├─ class_sections (1:N)
  ├─ enrollments (1:N)
  ├─ facilitators (M:N via FacilitatorSchool)
  └─ calendar_entries (1:N)
```

### Class & Student Management
```
ClassSection (class_level, section, academic_year)
  ├─ enrollments (1:N)
  ├─ planned_sessions (1:N)
  └─ calendar_sessions (M:N via CalendarDate)

Student (enrollment_number, full_name, dob, gender)
  └─ enrollments (1:N)

Enrollment (student + class_section + school)
  ├─ student (FK)
  ├─ school (FK)
  ├─ class_section (FK)
  └─ attendances (1:N)
```

### Session Execution Flow
```
PlannedSession (day_number, title, sequence_position)
  ├─ steps (1:N) → SessionStep (order, subject, duration)
  ├─ actual_sessions (1:N) → ActualSession (date, facilitator, status)
  │   ├─ attendances (1:N) → Attendance (student, status)
  │   ├─ feedback (1:1) → SessionFeedback (facilitator feedback)
  │   ├─ student_feedback (1:N) → StudentFeedback (anonymous)
  │   ├─ rewards (1:N) → SessionReward (photos, descriptions)
  │   ├─ facilitator_tasks (1:N) → FacilitatorTask (media, links)
  │   └─ cancellation (1:1) → SessionCancellation (reason, permanent)
  ├─ lesson_plan_uploads (1:N) → LessonPlanUpload (file, approval)
  └─ preparation_checklists (1:N) → SessionPreparationChecklist (checkpoints)
```

### Curriculum & Content
```
CurriculumSession (day_number, language, content, status)
  ├─ planned_sessions (1:N) (reverse)
  ├─ session_usage_logs (1:N) → SessionUsageLog (facilitator access)
  ├─ curriculum_usage_logs (1:N) → CurriculumUsageLog (detailed tracking)
  └─ version_history (1:N) → SessionVersionHistory (audit trail)

SessionTemplate (name, language, content_structure)
  └─ sessions (1:N) (reverse)

SessionContentMapping (1:1 with PlannedSession)
  ├─ planned_session (OneToOne)
  └─ curriculum_session (FK)
```

### Feedback & Analytics
```
SessionFeedback (1:1 with ActualSession)
  ├─ actual_session (OneToOne)
  ├─ facilitator (FK)
  └─ Fields: engagement, understanding, completion %, ratings

StudentFeedback (1:N with ActualSession)
  ├─ actual_session (FK)
  └─ Fields: rating, understanding, clarity, suggestions

FeedbackAnalytics (1:1 with ActualSession)
  ├─ actual_session (OneToOne)
  └─ Calculated: average_rating, understanding_%, clarity_%, quality_score
```

### Performance Tracking
```
Subject (name, code, description)
  └─ student_performances (1:N)

StudentPerformance (student + subject + class_section)
  ├─ student (FK)
  ├─ subject (FK)
  ├─ class_section (FK)
  └─ Fields: score, grade (auto-calculated), remarks

StudentPerformanceSummary (1:1 with Student per class)
  ├─ student (OneToOne)
  ├─ class_section (FK)
  └─ Fields: average_score, rank, passed_subjects, is_passed

PerformanceCutoff (1:1 with ClassSection)
  ├─ class_section (OneToOne)
  └─ Fields: passing_score, good_score, excellent_score
```

### Calendar & Scheduling
```
SupervisorCalendar (1:1 with User)
  ├─ supervisor (OneToOne)
  └─ dates (1:N) → CalendarDate

CalendarDate (date, date_type, time)
  ├─ calendar (FK)
  ├─ class_sections (M:M)
  ├─ school (FK)
  ├─ assigned_facilitators (M:M)
  └─ attendance_records (1:N) → OfficeWorkAttendance

OfficeWorkAttendance (calendar_date + facilitator)
  ├─ calendar_date (FK)
  ├─ facilitator (FK)
  └─ Fields: status (present/absent), remarks
```

---

## Key Connection Logic

### 1. User Role Hierarchy
```python
# Admin (role_id=0)
# - Full system access
# - Can manage all schools, facilitators, supervisors

# Supervisor (role_id=1)
# - Manages facilitators (via User.supervisor FK)
# - Manages schools assigned to them
# - Views reports for their schools
# - Has SupervisorCalendar for scheduling

# Facilitator (role_id=2)
# - Assigned to schools via FacilitatorSchool
# - Conducts sessions (ActualSession.facilitator)
# - Marks attendance
# - Provides feedback
# - Uploads lesson plans
```

### 2. Session Execution Pipeline
```
1. Admin creates PlannedSession (day_number, title)
   └─ Optionally links to CurriculumSession

2. Admin creates SessionStep entries (order, subject, duration)
   └─ Each step has activities/content

3. Supervisor schedules on CalendarDate
   └─ Links PlannedSession to specific date

4. Facilitator conducts session
   └─ Creates ActualSession (date, facilitator, status)
   └─ Marks Attendance for each student
   └─ Provides SessionFeedback
   └─ Uploads LessonPlanUpload (optional)
   └─ Creates SessionReward (optional)

5. Analytics calculated
   └─ FeedbackAnalytics aggregates feedback
   └─ Reports generated from Attendance + Feedback
```

### 3. Attendance Denormalization
```python
# Attendance table has denormalized fields for performance:
# - student_id (from enrollment.student_id)
# - class_section_id (from enrollment.class_section_id)
# - school_id (from enrollment.school_id)

# This allows fast queries like:
# Attendance.objects.filter(school_id=X, marked_at__date=Y)
# Without joining through Enrollment → ClassSection → School
```

### 4. Curriculum Content Resolution
```python
# PlannedSession can link to CurriculumSession
# If CurriculumSession exists:
#   - Use admin-managed content
#   - Track usage via CurriculumUsageLog
#   - Maintain version history

# If CurriculumSession doesn't exist:
#   - Fall back to static content
#   - SessionContentMapping.content_source = 'static_fallback'
#   - No usage tracking
```

### 5. Grouped Sessions
```python
# PlannedSession.grouped_session_id allows multiple classes
# to share the same session on the same date

# CalendarDate.class_sections (M:M) supports this
# Multiple ClassSections can be linked to one CalendarDate
```

### 6. Cancellation Tracking
```python
# ActualSession.status = CANCELLED triggers:
# 1. Create SessionCancellation record (OneToOne)
# 2. Set is_permanent_cancellation = True
# 3. Set can_be_rescheduled = False
# 4. Record reason (school_shutdown, exam_period, etc.)

# Allows audit trail and prevents accidental re-enabling
```

---

## Critical Indexes for Performance

### Attendance Queries
```python
# Fast attendance reports by school/date
Index(fields=['school_id', 'marked_at'])
Index(fields=['class_section_id', 'marked_at'])
Index(fields=['student_id', 'marked_at'])
Index(fields=['status', 'marked_at'])
```

### Session Queries
```python
# Fast session lookups
Index(fields=['planned_session', 'status'])
Index(fields=['date', 'status'])
Index(fields=['facilitator', 'date'])
```

### Enrollment Queries
```python
# Fast enrollment lookups
Index(fields=['is_active', 'school'])
Index(fields=['student', 'is_active'])
```

### Facilitator Assignment
```python
# Fast facilitator lookups
Index(fields=['is_active', 'school'])
Index(fields=['facilitator', 'is_active'])
```

---

## Data Integrity Rules

### Cascade Behavior
```
School deleted → ClassSection, Enrollment, FacilitatorSchool deleted
ClassSection deleted → Enrollment, PlannedSession deleted
PlannedSession deleted → SessionStep, ActualSession deleted
ActualSession deleted → Attendance, SessionFeedback, SessionReward deleted
Enrollment deleted → Attendance deleted
```

### Set Null Behavior
```
User deleted → ActualSession.facilitator = NULL
User deleted → ActualSession.status_changed_by = NULL
CurriculumSession deleted → PlannedSession.curriculum_session = NULL
SessionTemplate deleted → CurriculumSession.template = NULL
```

### Protect Behavior
```
Role deleted → ERROR (cannot delete if users exist)
```

---

## Unique Constraints

| Model | Constraint | Purpose |
|-------|-----------|---------|
| Role | name | Prevent duplicate role names |
| User | email | Unique login identifier |
| School | udise | Government ID uniqueness |
| Cluster | name | Unique cluster names |
| ClassSection | (school, class_level, section, academic_year) | Prevent duplicate classes |
| Student | enrollment_number | Unique student ID |
| Enrollment | (student, class_section, is_active) | One active enrollment per class |
| FacilitatorSchool | (facilitator, school) | One assignment per facilitator-school |
| PlannedSession | (class_section, day_number) | One day per class |
| SessionStep | (planned_session, order) | One step per order |
| ActualSession | (planned_session, date) | One session per day |
| Attendance | (actual_session, enrollment) | One attendance per student per session |
| CurriculumSession | (day_number, language) | One curriculum per day/language |
| LessonPlanUpload | (planned_session, facilitator) | One upload per facilitator per session |
| SessionFeedback | (actual_session, facilitator) | One feedback per facilitator per session |
| StudentFeedback | (actual_session, anonymous_student_id) | One feedback per student per session |
| PerformanceCutoff | class_section | One cutoff per class |
| StudentPerformance | (student, class_section, subject) | One score per student per subject |
| StudentPerformanceSummary | (student, class_section) | One summary per student per class |
| OfficeWorkAttendance | (calendar_date, facilitator) | One attendance per facilitator per date |

---

## Enum Choices

### SessionStatus
- 1 = CONDUCTED
- 2 = HOLIDAY
- 3 = CANCELLED

### AttendanceStatus
- 1 = PRESENT
- 2 = ABSENT
- 3 = LEAVE

### DateType
- 1 = SESSION (Planned Session)
- 2 = HOLIDAY (No Session)
- 3 = OFFICE_WORK (Task)

### CurriculumStatus
- 1 = DRAFT
- 2 = PUBLISHED
- 3 = ARCHIVED

### Cancellation Reasons
- school_shutdown
- syllabus_change
- exam_period
- duplicate_session
- emergency

---

## Total Model Count

**Core Models**: 35
- User Management: 2 (Role, User)
- Organization: 3 (Cluster, School, FacilitatorSchool)
- Classes: 1 (ClassSection)
- Students: 2 (Student, Enrollment)
- Sessions: 5 (PlannedSession, SessionStep, ActualSession, SessionCancellation, Attendance)
- Curriculum: 5 (CurriculumSession, SessionTemplate, SessionUsageLog, CurriculumUsageLog, SessionContentMapping)
- Lesson Planning: 1 (LessonPlanUpload)
- Feedback: 4 (SessionFeedback, StudentFeedback, SessionReward, SessionPreparationChecklist)
- Analytics: 1 (FeedbackAnalytics)
- Performance: 4 (Subject, PerformanceCutoff, StudentPerformance, StudentPerformanceSummary)
- Calendar: 3 (SupervisorCalendar, CalendarDate, OfficeWorkAttendance)
- Tasks: 1 (FacilitatorTask)

**Total Fields**: 350+  
**Total Relationships**: 60+  
**Total Indexes**: 25+  
**Total Unique Constraints**: 20+

