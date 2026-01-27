# CLAS Platform - Complete UI, Views & Services Guide

**Last Updated**: January 26, 2026  
**Framework**: Django + Tailwind CSS (Admin/Supervisor) + Bootstrap 5 (Facilitator)  
**Architecture**: Role-Based Access Control (RBAC)

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Role-Based Access Control](#role-based-access-control)
3. [Admin Views & UI](#admin-views--ui)
4. [Supervisor Views & UI](#supervisor-views--ui)
5. [Facilitator Views & UI](#facilitator-views--ui)
6. [Service Layer Logic](#service-layer-logic)
7. [AJAX Endpoints](#ajax-endpoints)
8. [Performance Optimizations](#performance-optimizations)
9. [Error Handling](#error-handling)

---

## Architecture Overview

### Technology Stack
- **Backend**: Django 4.x
- **Frontend**: 
  - **Admin**: Tailwind CSS + Material Icons + Inter Font
  - **Supervisor**: Tailwind CSS + Material Icons + Inter Font
  - **Facilitator**: Bootstrap 5.3.2 + Bootstrap Icons + Lexend Font
- **Database**: PostgreSQL
- **Caching**: Django Cache Framework (Redis/Memcached)
- **Authentication**: Django Auth + Custom User Model

### Project Structure
```
class/
├── views.py                    # Admin views (6564 lines)
├── supervisor_views.py         # Supervisor views (2028 lines)
├── facilitator_views.py        # Facilitator views (1158 lines)
├── reports_views.py            # Reports & Analytics
├── admin.py                    # Django Admin configuration
├── forms.py                    # Form definitions
├── models/                     # Database models
├── services/                   # Business logic layer
├── mixins.py                   # Reusable view mixins
├── decorators.py               # Custom decorators
└── Templates/
    ├── admin/                  # Admin templates
    ├── supervisor/             # Supervisor templates
    └── facilitator/            # Facilitator templates
```

---

## Role-Based Access Control

### Role Hierarchy
```
Admin (role_id=0)
  ├─ Full system access
  ├─ Manage all users, schools, classes
  ├─ View all reports
  └─ System configuration

Supervisor (role_id=1)
  ├─ Manage facilitators
  ├─ Manage assigned schools
  ├─ View school reports
  └─ Schedule sessions

Facilitator (role_id=2)
  ├─ Conduct sessions
  ├─ Mark attendance
  ├─ Provide feedback
  └─ View student performance
```

### Permission Decorators
```python
@login_required                    # Requires authentication
@supervisor_required               # Requires supervisor role
@facilitator_required              # Requires facilitator role
```

### Access Control Mixins
```python
FacilitatorAccessMixin             # Validates facilitator school access
PerformanceOptimizedMixin          # Query optimization
OptimizedListMixin                 # Pagination & filtering
CachedViewMixin                    # Caching layer
```

---

## CSS Framework & Base Templates

### Admin Role - Tailwind CSS
**Base Template**: `Templates/admin/shared/base.html`

**CSS Framework**: Tailwind CSS (CDN)
```html
<script src="https://cdn.tailwindcss.com"></script>
```

**Icons**: Material Symbols Outlined
```html
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet">
```

**Font**: Inter
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

**Key Features**:
- Responsive sidebar (280px desktop, fixed mobile)
- Smooth scrolling with hardware acceleration
- Mobile overlay for sidebar toggle
- Material Design icons
- Tailwind utility classes for styling
- PWA support with service worker registration
- Performance optimizations (requestAnimationFrame, passive event listeners)

**Layout Structure**:
```
app-container (flex)
├── sidebar (280px, responsive)
│   └── sidebar-nav (scrollable)
├── main-content (flex: 1)
    └── content-wrapper (scrollable)
        ├── messages (alerts)
        └── block content
```

**Color Scheme**:
- Primary: Blue (#3b82f6)
- Background: Gray (#f9fafb)
- Text: Gray (#1f2937)
- Borders: Gray (#e5e7eb)

**Responsive Breakpoints**:
- Mobile: < 1024px (sidebar slides from left)
- Desktop: ≥ 1024px (sidebar always visible)

---

### Supervisor Role - Tailwind CSS
**Base Template**: `Templates/supervisor/shared/base.html`

**CSS Framework**: Tailwind CSS (CDN)
```html
<script src="https://cdn.tailwindcss.com"></script>
```

**Icons**: Material Symbols Outlined
```html
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet">
```

**Font**: Inter
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

**Key Features**:
- Identical layout to Admin role
- Same responsive behavior
- Same Material Design icons
- Same performance optimizations
- PWA support

**Layout Structure**: Same as Admin

**Color Scheme**: Same as Admin

---

### Facilitator Role - Bootstrap 5
**Base Template**: `Templates/facilitator/shared/base.html`

**CSS Framework**: Bootstrap 5.3.2 (CDN)
```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
```

**Icons**: Bootstrap Icons
```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
```

**Font**: Lexend
```html
<link href="https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600;700&display=swap" rel="stylesheet"/>
```

**Key Features**:
- Responsive sidebar (280px desktop, fixed mobile)
- Bootstrap grid system
- Bootstrap components (buttons, cards, etc.)
- Bootstrap Icons for UI elements
- Mobile overlay for sidebar toggle
- PWA support with service worker registration

**Layout Structure**:
```
layout-wrapper (flex)
├── sidebar (280px, responsive)
│   ├── sidebar-user (profile section)
│   ├── sidebar-nav (scrollable)
│   │   ├── nav-section-label
│   │   └── nav-item (links)
│   └── sidebar-bottom (account section)
├── main-content (flex: 1)
    ├── topbar (header)
    │   ├── topbar-left (menu toggle, search)
    │   └── topbar-right (profile avatar)
    └── content (scrollable)
        └── block content
```

**Color Scheme**:
- Primary: Gray (#1f2937)
- Background: Light Gray (#f5f7f8)
- Text: Gray (#1f2937)
- Borders: Gray (#e5e7eb)
- Accent: Red (#dc2626) for logout

**Responsive Breakpoints**:
- Mobile: < 992px (sidebar slides from left)
- Desktop: ≥ 992px (sidebar always visible)

**Custom CSS Classes**:
- `.sidebar`: Main sidebar container
- `.sidebar-user`: User profile section
- `.sidebar-nav`: Navigation menu
- `.nav-item`: Navigation links
- `.nav-item.active`: Active navigation state
- `.topbar`: Header bar
- `.menu-toggle`: Mobile menu button
- `.search-box`: Search input
- `.profile-avatar`: User avatar
- `.overlay`: Mobile overlay

---

## Base Template Comparison

| Feature | Admin (Tailwind) | Supervisor (Tailwind) | Facilitator (Bootstrap) |
|---------|------------------|----------------------|------------------------|
| CSS Framework | Tailwind CSS | Tailwind CSS | Bootstrap 5.3.2 |
| Icons | Material Symbols | Material Symbols | Bootstrap Icons |
| Font | Inter | Inter | Lexend |
| Sidebar Width | 280px | 280px | 280px |
| Mobile Breakpoint | 1024px | 1024px | 992px |
| Topbar | No | No | Yes |
| Search Box | No | No | Yes (mobile hidden) |
| User Profile | Sidebar only | Sidebar only | Sidebar + Topbar |
| Color Scheme | Blue primary | Blue primary | Gray primary |
| PWA Support | Yes | Yes | Yes |
| Service Worker | Yes | Yes | Yes |

---

## Admin Views & UI

### Dashboard (`/admin/dashboard/`)
**File**: `class/views.py` (line ~2867)

**Purpose**: System overview with key metrics

**Features**:
- Total users, schools, classes count
- Recent activities
- System statistics
- Quick actions

**Template**: `admin/dashboard.html`

**Key Metrics**:
```python
{
    'total_users': User.objects.count(),
    'total_schools': School.objects.count(),
    'total_classes': ClassSection.objects.count(),
    'active_facilitators': User.objects.filter(role__id=2, is_active=True).count(),
    'recent_users': User.objects.order_by('-created_at')[:5],
    'recent_schools': School.objects.order_by('-created_at')[:5],
}
```

---

### User Management

#### List Users (`/admin/users/`)
**View**: `users_view()`

**Features**:
- Display all users with roles
- Filter by role
- Search functionality
- Pagination (20 per page)

**Template**: `admin/users/users.html`

**Query Optimization**:
```python
users = User.objects.all().select_related('role').order_by("-created_at")
```

#### Add User (`/admin/users/add/`)
**View**: `add_user()`

**Form**: `AddUserForm`

**Fields**:
- Email (unique)
- Full Name
- Password
- Role (dropdown)

**Validation**:
- Email uniqueness
- Password strength
- Role selection

#### Edit User (`/admin/users/edit/<user_id>/`)
**View**: `edit_user()`

**Form**: `EditUserForm`

**Features**:
- Update user details
- Change role
- Activate/deactivate

#### Delete User (`/admin/users/delete/<user_id>/`)
**View**: `delete_user()`

**Safety**:
- Confirmation required
- Cascade delete related records

---

### School Management

#### List Schools (`/admin/schools/`)
**View**: `schools()`

**Features**:
- Display all schools
- Show class count, student count, facilitator count
- Pagination (20 per page)
- Caching (5 minutes)

**Template**: `admin/schools/list.html`

**Query Optimization**:
```python
schools = School.objects.select_related().prefetch_related(
    Prefetch('class_sections', ...),
    Prefetch('facilitators', ...)
).annotate(
    total_classes=Count('class_sections', distinct=True),
    total_students=Count('class_sections__enrollments', distinct=True),
    active_facilitators=Count('facilitators', distinct=True)
)
```

**Cache Key**: `schools_list_{user_id}`

#### Add School (`/admin/schools/add/`)
**View**: `add_school()`

**Form**: `AddSchoolForm`

**Fields**:
- School Name
- UDISE Code (unique)
- Block, District, State
- Contact Person, Phone, Email
- Coordinates (latitude, longitude)
- Logo, Profile Image

#### Edit School (`/admin/schools/edit/<school_id>/`)
**View**: `edit_school()`

**Features**:
- Update school details
- Change cluster assignment
- Update contact information

#### School Detail (`/admin/schools/detail/<school_id>/`)
**View**: `school_detail()`

**Shows**:
- School information
- Class sections
- Facilitator assignments
- Student count
- Attendance statistics

**Template**: `admin/schools/detail.html`

**Calculations**:
```python
total_students = Enrollment.objects.filter(
    class_section__school=school,
    is_active=True
).values('student').distinct().count()

attendance_percentage = (present_count / total_attendance_records) * 100
```

---

### Class Management

#### List Classes (`/admin/classes/`)
**View**: `class_sections_list()`

**Features**:
- Display all classes
- Filter by school
- Custom ordering (class_level_order)
- Pagination (30 per page)

**Template**: `admin/classes/list.html`

**Ordering Logic**:
```python
class_sections = sorted(
    class_sections, 
    key=lambda x: (x.school.name, x.class_level_order, x.section or 'A')
)
```

#### Add Class (`/admin/classes/add/<school_id>/`)
**View**: `class_section_add()`

**Form**: `ClassSectionForm`

**Fields**:
- Class Level (LKG, UKG, 1-10)
- Section (A, B, C, etc.)
- Academic Year

**Validation**:
- Duplicate check (school + class_level + section + academic_year)

#### Bulk Create Classes (`/admin/classes/bulk-create/`)
**View**: `admin_bulk_create_classes()`

**Features**:
- Create multiple classes at once
- Maximum 10 classes per batch
- School selection
- Validation for each class

**Template**: `admin/classes/bulk_create.html`

---

### Student Management

#### List Students (`/admin/students/<school_id>/`)
**View**: `students_list()`

**Features**:
- Display students by school
- Filter by class section
- Pagination (50 per page)
- Show enrollment details

**Template**: `admin/students/students_list.html`

#### Add Student (`/admin/students/add/<school_id>/`)
**View**: `student_add()`

**Fields**:
- Enrollment Number (unique)
- Full Name
- Gender
- Class Section
- Start Date

**Logic**:
```python
# Get or create student
student, _ = Student.objects.get_or_create(
    enrollment_number=request.POST["enrollment_number"],
    defaults={...}
)

# Create enrollment
Enrollment.objects.get_or_create(
    student=student,
    school=school,
    class_section_id=request.POST["class_section"],
    defaults={...}
)
```

#### Edit Student (`/admin/students/edit/<school_id>/<student_id>/`)
**View**: `student_edit()`

**Features**:
- Update student details
- Change class section
- Update enrollment dates

---

### Reports & Analytics

#### Reports Dashboard (`/admin/reports/`)
**View**: `reports_dashboard()`

**Features**:
- Report type selection
- Date range filters
- School/Class filters
- Export options (PDF, Excel)

**Template**: `admin/reports/dashboard.html`

#### Report Types

##### 1. Students Report
**View**: `get_students_report_data()`

**Data**:
- Student name, enrollment number
- Class, school
- Attendance (present, absent, percentage)
- Last session date

**Query Optimization**:
```python
# Batch query for attendance stats
attendance_stats = Attendance.objects.filter(
    enrollment_id__in=enrollment_ids
).values('enrollment_id').annotate(
    present_count=Count('id', filter=Q(status=1)),
    absent_count=Count('id', filter=Q(status=2))
)
```

##### 2. Facilitators Report
**View**: `get_facilitators_report_data()`

**Data**:
- Facilitator name, email
- Schools assigned
- Sessions conducted
- Average rating
- Last active date

##### 3. Attendance Report
**View**: `get_attendance_report_data()`

**Data**:
- Date, school, class
- Total students, present, absent
- Attendance percentage
- Facilitator name

**Charts**:
- Daily attendance trend
- Class-wise attendance comparison

##### 4. Sessions Report
**View**: `get_sessions_report_data()`

**Data**:
- Date, topic, day number
- Class, facilitator
- Status, duration

##### 5. Feedback Report
**View**: `get_feedback_report_data()`

**Data**:
- Date, session topic
- Facilitator, rating
- Feedback text

#### Export Functions

##### PDF Export
**View**: `download_pdf_report()`

**Features**:
- ReportLab for PDF generation
- Formatted tables
- Header/footer
- Date range info

**File**: `{report_type}_report_{YYYYMMDD}.pdf`

##### Excel Export
**View**: `download_excel_report()`

**Features**:
- OpenPyXL for Excel generation
- Styled headers
- Auto-adjusted columns
- Multiple sheets

**File**: `{report_type}_report_{YYYYMMDD}.xlsx`

---

## Supervisor Views & UI

### Dashboard (`/supervisor/dashboard/`)
**View**: `supervisor_dashboard()`

**Purpose**: Supervisor overview of managed resources

**Metrics**:
```python
{
    'total_schools': School.objects.count(),
    'active_schools': School.objects.filter(status=1).count(),
    'total_classes': ClassSection.objects.count(),
    'active_classes': ClassSection.objects.filter(is_active=True).count(),
    'active_facilitators': User.objects.filter(role__id=2, is_active=True).count(),
}
```

**Template**: `supervisor/dashboard.html`

---

### User Management

#### List Users (`/supervisor/users/`)
**View**: `supervisor_users_list()`

**Features**:
- Filter by role
- Filter by status (active/inactive)
- Pagination

**Template**: `supervisor/users/list.html`

#### Create User (`/supervisor/users/create/`)
**View**: `supervisor_user_create()`

**Form**: `AddUserForm`

#### Edit User (`/supervisor/users/edit/<user_id>/`)
**View**: `supervisor_user_edit()`

#### Delete User (`/supervisor/users/delete/<user_id>/`)
**View**: `supervisor_user_delete()`

---

### School Management

#### List Schools (`/supervisor/schools/`)
**View**: `supervisor_schools_list()`

**Features**:
- Display all schools
- Filter by status
- Show class count, student count, facilitator count
- Caching (5 minutes)

**Template**: `supervisor/schools/list.html`

**Cache Key**: `supervisor_schools_list_{user_id}`

#### Create School (`/supervisor/schools/create/`)
**View**: `supervisor_school_create()`

#### Edit School (`/supervisor/schools/edit/<school_id>/`)
**View**: `supervisor_school_edit()`

**Features**:
- Update school details
- Get existing blocks for district (AJAX)

#### School Detail (`/supervisor/schools/detail/<school_id>/`)
**View**: `supervisor_school_detail()`

#### Delete School (`/supervisor/schools/delete/<school_id>/`)
**View**: `supervisor_school_delete()`

---

### Class Management

#### List Classes (`/supervisor/classes/`)
**View**: `supervisor_classes_list()`

**Features**:
- Filter by school
- Show enrollment count
- Caching

**Template**: `supervisor/classes/list.html`

---

### Facilitator Management

#### List Facilitators (`/supervisor/facilitators/`)
**View**: `supervisor_facilitators_list()`

**Features**:
- Display all facilitators
- Show schools assigned
- Show sessions conducted
- Show feedback count
- Filter by status

**Template**: `supervisor/facilitators/list.html`

**Batch Queries**:
```python
# Get session counts per facilitator
session_counts = ActualSession.objects.filter(
    facilitator_id__in=facilitator_ids,
    status=1
).values('facilitator_id').annotate(count=Count('id'))

# Get unique student counts
strength_counts = Attendance.objects.filter(
    actual_session__facilitator_id__in=facilitator_ids
).values('actual_session__facilitator_id').annotate(
    unique_students=Count('enrollment__student', distinct=True)
)

# Get feedback counts
feedback_counts = SessionFeedback.objects.filter(
    facilitator_id__in=facilitator_ids
).values('facilitator_id').annotate(count=Count('id'))
```

#### Facilitator Detail (`/supervisor/facilitators/<facilitator_id>/`)
**View**: `supervisor_facilitator_detail()`

**Shows**:
- Facilitator profile
- Assigned schools and classes
- Recent students (15)
- Task submissions (filtered by date)
- Feedback records
- Attendance statistics

**Template**: `supervisor/facilitators/detail.html`

**Date Filtering**:
```python
# Get tasks for specific date
if selected_task_date:
    facilitator_tasks = FacilitatorTask.objects.filter(
        facilitator=facilitator,
        created_at__date=task_date_obj
    )
```

---

### Reports & Analytics

#### Reports Dashboard (`/supervisor/reports/`)
**View**: `supervisor_reports_dashboard()`

**Features**:
- User breakdown by role
- Schools by status
- Basic statistics

**Template**: `supervisor/reports/dashboard.html`

#### Feedback Analytics (`/supervisor/reports/feedback/`)
**View**: `supervisor_feedback_analytics()`

**Template**: `supervisor/reports/feedback.html`

---

### AJAX Endpoints

#### Get Blocks by District
**Endpoint**: `/supervisor/ajax/blocks-by-district/`

**View**: `get_blocks_by_district()`

**Parameters**:
- `district`: District name

**Response**:
```json
{
    "blocks": ["Block A", "Block B", "Block C"]
}
```

#### Get Schools by Block
**Endpoint**: `/supervisor/ajax/schools-by-block/`

**View**: `get_schools_by_block()`

**Parameters**:
- `district`: District name
- `block`: Block name

**Response**:
```json
{
    "schools": [
        {"id": "uuid", "name": "School Name", "latitude": 28.7041, "longitude": 77.1025}
    ]
}
```

#### Get All Schools
**Endpoint**: `/supervisor/ajax/all-schools/`

**View**: `get_all_schools()`

**Response**:
```json
{
    "schools": [
        {"id": "uuid", "name": "School Name", "district": "District", "block": "Block", "latitude": 28.7041, "longitude": 77.1025}
    ]
}
```

#### Create User (AJAX)
**Endpoint**: `/supervisor/ajax/create-user/`

**View**: `supervisor_create_user_ajax()`

**Parameters**:
- `full_name`: User's full name
- `email`: User's email
- `password`: User's password
- `role`: Role ID

**Response**:
```json
{
    "success": true,
    "user": {
        "id": "uuid",
        "full_name": "Name",
        "email": "email@example.com",
        "role_name": "Facilitator"
    }
}
```

---

## Facilitator Views & UI

### Dashboard (`/facilitator/dashboard/`)
**View**: `facilitator_dashboard()`

**Purpose**: Facilitator overview of their work

**Metrics**:
```python
{
    'total_schools': facilitator_schools.count(),
    'total_classes': facilitator_classes.count(),
    'total_students': Enrollment.objects.filter(school__in=facilitator_schools).count(),
    'total_planned_sessions': PlannedSession.objects.filter(class_section__in=facilitator_classes).count(),
    'conducted_sessions': ActualSession.objects.filter(status=1).count(),
    'session_completion_rate': (conducted / total) * 100,
    'overall_attendance_rate': (present / total_attendance) * 100,
}
```

**Template**: `facilitator/dashboard.html`

**Class-wise Attendance Stats**:
```python
class_attendance_stats = []
for class_section in facilitator_classes[:5]:
    class_attendance_rate = (present_count / total_count) * 100
    class_attendance_stats.append({
        'class_section': class_section,
        'attendance_rate': round(class_attendance_rate, 1),
        'total_students': Enrollment.objects.filter(class_section=class_section).count()
    })
```

---

### School Management

#### List Schools (`/facilitator/schools/`)
**View**: `FacilitatorSchoolListView`

**Features**:
- Display assigned schools
- Show enrollment count, class count
- Batch queries for performance

**Template**: `facilitator/schools/list.html`

**Query Optimization**:
```python
# Batch query for enrollment counts
enrollment_counts = Enrollment.objects.filter(
    school_id__in=school_ids,
    is_active=True
).values('school_id').annotate(count=Count('id'))

# Batch query for class counts
class_counts = ClassSection.objects.filter(
    school_id__in=school_ids,
    is_active=True
).values('school_id').annotate(count=Count('id'))
```

#### School Detail (`/facilitator/schools/<school_id>/`)
**View**: `FacilitatorSchoolDetailView`

**Features**:
- Display classes in school
- Filter by grade level
- Show enrollment count per class

**Template**: `facilitator/schools/detail.html`

---

### Student Management

#### List Students (`/facilitator/students/`)
**View**: `FacilitatorStudentListView`

**Features**:
- Display students from assigned schools
- Filter by school, class, grade
- Search by name or enrollment number
- Pagination (20 per page)
- Show attendance statistics

**Template**: `facilitator/students/list.html`

**Filters**:
```python
queryset = Enrollment.objects.filter(
    is_active=True,
    school__in=self.get_facilitator_schools()
)

# Apply filters
if school_filter:
    queryset = queryset.filter(school_id=school_filter)
if class_filter:
    queryset = queryset.filter(class_section_id=class_filter)
if grade_filter:
    queryset = queryset.filter(class_section__class_level=grade_filter)
if search_query:
    queryset = queryset.filter(
        Q(student__full_name__icontains=search_query) |
        Q(student__enrollment_number__icontains=search_query)
    )
```

**Attendance Statistics** (Batch Query):
```python
# Get attendance stats for all enrollments in one query
attendance_stats = Attendance.objects.filter(
    enrollment_id__in=enrollment_ids
).values('enrollment_id').annotate(
    present_count=Count('id', filter=Q(status=1)),
    absent_count=Count('id', filter=Q(status=2))
)

# Convert to dict for quick lookup
attendance_by_enrollment = {
    stat['enrollment_id']: {
        'present': stat['present_count'],
        'absent': stat['absent_count']
    }
    for stat in attendance_stats
}
```

#### Create Student (`/facilitator/students/create/`)
**View**: `FacilitatorStudentCreateView`

**Form**: Student creation form

**Fields**:
- Enrollment Number
- Full Name
- Gender
- Class Section (dropdown)

**Logic**:
```python
# Create student
student = form.save()

# Create enrollment with start_date
Enrollment.objects.create(
    student=student,
    school=class_section.school,
    class_section=class_section,
    start_date=date.today(),
    is_active=True
)
```

#### Edit Student (`/facilitator/students/edit/<student_id>/`)
**View**: `FacilitatorStudentUpdateView`

**Features**:
- Update student details
- Change class section
- Update enrollment

#### Student Detail (`/facilitator/students/<student_id>/`)
**View**: `facilitator_student_detail()`

**Shows**:
- Student information
- Enrollment details
- Attendance statistics
- Recent attendance records

**Template**: `facilitator/students/detail.html`

**Calculations**:
```python
total_sessions = ActualSession.objects.filter(
    planned_session__class_section=enrollment.class_section,
    status=1
).count()

present_count = Attendance.objects.filter(
    enrollment=enrollment,
    status=1
).count()

attendance_percentage = (present_count / total_sessions) * 100
```

---

### Today's Session

#### Today's Session Calendar (`/facilitator/today-session/`)
**View**: `facilitator_today_session_calendar()`

**Purpose**: Show today's scheduled sessions

**Features**:
- Display only today's sessions
- Show grouped sessions
- Mark attendance
- Submit feedback

**Template**: `facilitator/Today_session.html`

**Optimization**:
```python
# Only get calendar entries for TODAY
calendar_sessions_today = CalendarDate.objects.filter(
    date=today,
    date_type=DateType.SESSION
).select_related('school', 'calendar__supervisor').prefetch_related('class_sections')
```

---

## Service Layer Logic

### Session Integration Service
**File**: `class/services/session_integration_service.py`

**Purpose**: Centralized session management logic

**Key Classes**:

#### SessionIntegrationService
```python
class SessionIntegrationService:
    @staticmethod
    def get_integrated_session_data(planned_session):
        """Get complete session data with curriculum content"""
        # Get curriculum content if linked
        # Get session steps
        # Get attendance data
        # Get feedback data
        # Return integrated data
    
    @staticmethod
    def create_session_with_curriculum(class_section, day_number, curriculum_session):
        """Create planned session linked to curriculum"""
        # Create PlannedSession
        # Link to CurriculumSession
        # Create SessionSteps from curriculum
        # Return created session
```

### Session Management Classes
**File**: `class/session_management.py`

#### SessionSequenceCalculator
```python
class SessionSequenceCalculator:
    @staticmethod
    def calculate_sequence_position(class_section, day_number):
        """Calculate sequence position for a session"""
        # Get all sessions for class
        # Calculate position based on day_number
        # Return position
    
    @staticmethod
    def get_prerequisite_days(day_number):
        """Get prerequisite days for a session"""
        # Return list of days that must be completed first
```

#### SessionStatusManager
```python
class SessionStatusManager:
    @staticmethod
    def update_session_status(actual_session, new_status, reason=None):
        """Update session status with audit trail"""
        # Update status
        # Record who changed it and why
        # Update related records
        # Return updated session
    
    @staticmethod
    def can_cancel_session(actual_session):
        """Check if session can be cancelled"""
        # Check if attendance already marked
        # Check if feedback already submitted
        # Return boolean
```

---

## AJAX Endpoints

### Admin AJAX

#### Create User (AJAX)
**Endpoint**: `/admin/ajax/create-user/`

**View**: `create_user_ajax()`

**Parameters**:
- `full_name`: User's full name
- `email`: User's email
- `password`: User's password
- `role`: Role ID

**Response**:
```json
{
    "success": true,
    "user": {
        "id": "uuid",
        "full_name": "Name",
        "email": "email@example.com",
        "role_name": "Facilitator"
    }
}
```

### Facilitator AJAX

#### Get School Classes
**Endpoint**: `/facilitator/ajax/school-classes/`

**View**: `facilitator_ajax_school_classes()`

**Parameters**:
- `school_id`: School UUID

**Response**:
```json
{
    "success": true,
    "classes": [
        {
            "id": "uuid",
            "class_level": "1",
            "section": "A",
            "display_name": "1A"
        }
    ],
    "count": 5
}
```

#### Debug Schools
**Endpoint**: `/facilitator/debug/schools/`

**View**: `facilitator_debug_schools()`

**Purpose**: Debug facilitator school access

**Response**:
```json
{
    "facilitator_id": "uuid",
    "facilitator_name": "Name",
    "schools_count": 3,
    "schools": [
        {
            "id": "uuid",
            "name": "School Name",
            "class_count": 5,
            "classes": [...]
        }
    ]
}
```

#### Test Access
**Endpoint**: `/facilitator/test-access/`

**View**: `facilitator_test_access()`

**Purpose**: Test facilitator access with HTML interface

**Returns**: HTML page with access information and AJAX test tool

---

## Performance Optimizations

### Query Optimization Techniques

#### 1. Select Related
```python
# Reduces N+1 queries for ForeignKey relationships
users = User.objects.select_related('role')
```

#### 2. Prefetch Related
```python
# Reduces N+1 queries for reverse ForeignKey and M2M
schools = School.objects.prefetch_related(
    Prefetch('class_sections', queryset=ClassSection.objects.filter(is_active=True))
)
```

#### 3. Batch Queries
```python
# Get all data in one query instead of N queries
enrollment_counts = Enrollment.objects.filter(
    school_id__in=school_ids
).values('school_id').annotate(count=Count('id'))

# Convert to dict for O(1) lookup
enrollment_by_school = {item['school_id']: item['count'] for item in enrollment_counts}
```

#### 4. Aggregation
```python
# Use aggregation instead of count() for better performance
stats = User.objects.aggregate(
    active_facilitators=Count('id', filter=Q(role__id=2, is_active=True))
)
```

### Caching Strategy

#### Cache Keys
```python
# School list cache
cache_key = f"schools_list_{user_id}"
cache.set(cache_key, schools_queryset, 300)  # 5 minutes

# Supervisor schools cache
cache_key = f"supervisor_schools_list_{user_id}"

# All schools cache
cache_key = "supervisor_schools_all"
```

#### Cache Invalidation
```python
# Clear cache when data changes
cache.delete(f"schools_list_{user_id}")
cache.delete(f"supervisor_schools_list_{user_id}")
```

### Pagination
```python
# Limit results per page
paginator = Paginator(queryset, 20)  # 20 items per page
page_obj = paginator.get_page(page_number)
```

---

## Error Handling

### Permission Errors
```python
# Redirect to no permission page
if request.user.role.name.upper() != "ADMIN":
    messages.error(request, "You do not have permission to access this page.")
    return redirect("no_permission")
```

### 404 Errors
```python
# Get object or return 404
school = get_object_or_404(School, id=school_id)
```

### Validation Errors
```python
# Form validation
if form.is_valid():
    form.save()
else:
    # Display form errors
    return render(request, template, {'form': form})
```

### Database Errors
```python
# Transaction handling
try:
    with transaction.atomic():
        # Create multiple records
        PlannedSession.objects.bulk_create(sessions_to_create)
except Exception as e:
    return {'success': False, 'error': str(e)}
```

---

## Summary

**Total Views**: 100+  
**Total Templates**: 50+  
**Total AJAX Endpoints**: 15+  
**Performance Optimizations**: 20+  
**Caching Strategies**: 5+

This comprehensive guide covers all UI, views, and service logic for the CLAS platform across all three user roles (Admin, Supervisor, Facilitator).

