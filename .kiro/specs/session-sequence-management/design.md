# Design Document

## Overview

The Session Sequence Management system ensures perfect 1-150 day curriculum progression for all class sections. The design implements a robust session tracking mechanism that prevents session skipping, maintains sequence integrity, and provides clear facilitator guidance for daily session execution.

The system builds upon the existing PlannedSession and ActualSession models while adding enhanced logic for sequence management, status tracking, and progress monitoring. The solution ensures that every facilitator always sees the correct "next session" without any possibility of missing curriculum days.

## Architecture

The system follows a layered architecture with enhanced session management:

### Session Sequence Layer
- **Sequence Calculator**: Determines the next pending session for any class
- **Status Manager**: Handles session status transitions and validation
- **Progress Tracker**: Monitors completion progress and generates metrics

### Business Logic Layer
- **Session Controller**: Manages session execution workflow
- **Validation Engine**: Ensures sequence integrity and prevents gaps
- **Notification System**: Alerts for sequence issues or completion milestones

### Data Persistence Layer
- **Enhanced Models**: Extended session models with sequence tracking
- **Integrity Constraints**: Database-level sequence validation
- **Audit Trail**: Complete history of all session status changes

## Components and Interfaces

### SessionSequenceCalculator
**Purpose**: Determines the correct "today's session" for any class section
**Key Methods**:
- `get_next_pending_session()`: Returns the next session that needs to be conducted
- `validate_sequence_integrity()`: Checks for gaps or issues in the session sequence
- `calculate_progress()`: Computes completion percentage and metrics

**Interface**:
```python
class SessionSequenceCalculator:
    def get_next_pending_session(class_section: ClassSection) -> PlannedSession
    def validate_sequence_integrity(class_section: ClassSection) -> ValidationResult
    def calculate_progress(class_section: ClassSection) -> ProgressMetrics
    def get_session_history(class_section: ClassSection) -> List[SessionRecord]
```

### SessionStatusManager
**Purpose**: Manages session status transitions and business rules
**Key Methods**:
- `conduct_session()`: Marks session as conducted and creates attendance records
- `mark_holiday()`: Marks session as holiday while preserving for future conduct
- `cancel_session()`: Permanently cancels session and moves to next day
- `validate_status_change()`: Ensures status transitions are valid

**Interface**:
```python
class SessionStatusManager:
    def conduct_session(planned_session: PlannedSession, facilitator: User) -> ActualSession
    def mark_holiday(planned_session: PlannedSession, reason: str) -> ActualSession
    def cancel_session(planned_session: PlannedSession, reason: str) -> ActualSession
    def validate_status_change(current_status: str, new_status: str) -> bool
```

### SessionBulkManager
**Purpose**: Handles bulk operations on sessions across multiple classes
**Key Methods**:
- `generate_sessions_for_class()`: Auto-creates 1-150 sessions for new class
- `bulk_delete_sessions()`: Deletes sessions with confirmation and impact analysis
- `apply_template_to_classes()`: Applies session templates to multiple classes
- `delete_day_from_all_classes()`: Removes specific day from all classes

**Interface**:
```python
class SessionBulkManager:
    def generate_sessions_for_class(class_section: ClassSection, template: SessionTemplate = None) -> GenerationResult
    def bulk_delete_sessions(class_sections: List[ClassSection], options: dict) -> BulkResult
    def apply_template_to_classes(template: SessionTemplate, classes: List[ClassSection]) -> ApplicationResult
    def delete_day_from_all_classes(day_number: int, school: School = None) -> DeletionResult
```

### SessionTemplateImporter
**Purpose**: Imports and applies session templates from external sources
**Key Methods**:
- `import_template_file()`: Imports session templates from CSV/Excel files
- `validate_template_structure()`: Validates template format and content
- `apply_template_bulk()`: Applies templates to multiple classes efficiently
- `generate_import_report()`: Creates detailed import operation reports

**Interface**:
```python
class SessionTemplateImporter:
    def import_template_file(file: UploadedFile, options: dict) -> ImportResult
    def validate_template_structure(template_data: dict) -> ValidationResult
    def apply_template_bulk(template: SessionTemplate, targets: List[ClassSection]) -> BulkApplicationResult
    def generate_import_report(operation: ImportOperation) -> ImportReport
```

### AdminSessionController
**Purpose**: Provides admin-specific session management functionality
**Key Methods**:
- `get_class_session_overview()`: Returns complete session status for a class
- `perform_bulk_operation()`: Executes bulk operations with progress tracking
- `repair_session_sequence()`: Fixes sequence gaps and issues
- `generate_admin_reports()`: Creates management reports and analytics

**Interface**:
```python
class AdminSessionController:
    def get_class_session_overview(class_section: ClassSection) -> SessionOverview
    def perform_bulk_operation(operation: BulkOperation) -> OperationResult
    def repair_session_sequence(class_section: ClassSection) -> RepairResult
    def generate_admin_reports(filters: dict) -> AdminReports
```

## Data Models

### Enhanced PlannedSession
Extended with sequence tracking and validation:

```python
class PlannedSession(models.Model):
    # Existing fields
    class_section: ForeignKey
    day_number: int              # 1-150 sequence number
    title: str
    description: TextField
    is_active: bool
    
    # New sequence management fields
    sequence_position: int       # Enforced sequential position
    is_required: bool           # Cannot be skipped (default True)
    prerequisite_days: JSONField # Days that must be completed first
    created_at: datetime
    updated_at: datetime
    
    class Meta:
        unique_together = ('class_section', 'day_number')
        ordering = ['day_number']
```

### Enhanced ActualSession
Extended with detailed status tracking and cancellation reasons:

```python
class ActualSession(models.Model):
    # Existing fields
    planned_session: ForeignKey
    date: DateField
    facilitator: ForeignKey
    status: str                  # conducted, holiday, cancelled
    remarks: TextField
    created_at: datetime
    
    # Enhanced tracking fields
    conducted_at: datetime       # Exact time of conduct
    duration_minutes: int        # Session duration
    attendance_marked: bool      # Whether attendance was completed
    status_changed_by: ForeignKey # Who changed the status
    status_change_reason: TextField # Why status was changed
    can_be_rescheduled: bool    # For holiday sessions
    
    # Cancellation tracking
    cancellation_reason: str     # Predefined cancellation reasons
    cancellation_category: str   # school_shutdown, syllabus_change, exam_period, duplicate, emergency
    is_permanent_cancellation: bool # Cannot be undone
    
    class Meta:
        unique_together = ('planned_session', 'date')

# Cancellation reason choices
CANCELLATION_REASONS = [
    ('school_shutdown', 'School permanently shuts down for this class'),
    ('syllabus_change', 'Government removes topic from syllabus'),
    ('exam_period', 'Exam period replaces class permanently'),
    ('duplicate_session', 'Duplicate or wrongly created planned session'),
    ('emergency', 'Emergency where session will never happen again'),
]
```

### SessionTemplate
Enhanced template model for bulk session generation:

```python
class SessionTemplate(models.Model):
    name: str                    # Template name (e.g., "Standard CLAS Curriculum")
    description: TextField       # Template description
    language: str                # Target language (Hindi/English/Both)
    total_days: int             # Number of days in template (default 150)
    
    # Template structure
    day_templates: JSONField     # Day-wise content templates
    default_activities: JSONField # Standard activities per day
    learning_objectives: JSONField # Objectives for each day
    
    # Metadata
    created_by: ForeignKey       # Administrator who created template
    is_active: bool             # Whether template can be used
    usage_count: int            # Number of times applied
    created_at: datetime
    updated_at: datetime
```

### LessonPlanUpload
New model to track facilitator lesson plan uploads:

```python
class LessonPlanUpload(models.Model):
    planned_session: ForeignKey  # Reference to the session
    facilitator: ForeignKey      # Who uploaded the lesson plan
    upload_date: DateField       # When it was uploaded
    lesson_plan_file: FileField  # Uploaded lesson plan file
    file_name: str              # Original file name
    file_size: int              # File size in bytes
    upload_notes: TextField     # Optional notes from facilitator
    is_approved: bool           # Admin approval status
    approved_by: ForeignKey     # Admin who approved
    approved_at: datetime       # Approval timestamp
    
    class Meta:
        unique_together = ('planned_session', 'facilitator')
```

### SessionReward
New model to track student rewards:

```python
class SessionReward(models.Model):
    actual_session: ForeignKey   # Reference to the conducted session
    facilitator: ForeignKey      # Who gave the reward
    reward_type: str            # photo, text, both
    reward_photo: ImageField    # Photo of reward/student
    reward_description: TextField # Text description of reward
    student_names: TextField    # Names of students who received rewards
    reward_date: DateTimeField  # When reward was given
    is_visible_to_admin: bool   # Admin visibility
    admin_notes: TextField      # Admin comments on reward
    
    class Meta:
        ordering = ['-reward_date']
```

### SessionFeedback
New model for comprehensive session feedback:

```python
class SessionFeedback(models.Model):
    actual_session: ForeignKey   # Reference to conducted session
    facilitator: ForeignKey      # Who provided feedback
    
    # Student Analysis Feedback
    student_engagement_level: int # 1-5 scale
    student_understanding_level: int # 1-5 scale
    student_participation_notes: TextField
    learning_objectives_met: bool
    challenging_topics: TextField
    student_questions: TextField
    
    # Session Progress Feedback
    session_completion_percentage: int # 0-100%
    time_management_rating: int  # 1-5 scale
    content_difficulty_rating: int # 1-5 scale
    
    # Facilitator Personal Reflection
    facilitator_satisfaction: int # 1-5 scale
    what_went_well: TextField
    areas_for_improvement: TextField
    next_session_preparation: TextField
    additional_notes: TextField
    
    # Metadata
    feedback_date: DateTimeField
    is_complete: bool           # Whether all required fields are filled
    
    class Meta:
        unique_together = ('actual_session', 'facilitator')
```

### SessionPreparationChecklist
New model for session preparation tracking:

```python
class SessionPreparationChecklist(models.Model):
    planned_session: ForeignKey  # Reference to session
    facilitator: ForeignKey      # Who is preparing
    
    # Preparation Checkpoints
    lesson_plan_reviewed: bool
    materials_prepared: bool
    technology_tested: bool
    classroom_setup_ready: bool
    student_list_reviewed: bool
    previous_session_feedback_reviewed: bool
    
    # Checkpoint Timestamps
    checkpoints_completed_at: JSONField # Track when each checkpoint was completed
    preparation_start_time: DateTimeField
    preparation_complete_time: DateTimeField
    total_preparation_minutes: int
    
    # Preparation Notes
    preparation_notes: TextField
    anticipated_challenges: TextField
    special_requirements: TextField
    
    class Meta:
        unique_together = ('planned_session', 'facilitator')
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Core Properties

**Property 1: Session sequence completeness**
*For any* class section, there should be exactly 150 planned sessions with day numbers 1 through 150, with no gaps or duplicates
**Validates: Requirements 4.1, 4.3**

**Property 2: Next session calculation accuracy**
*For any* class section, the "today's session" should always be the lowest day number that has not been conducted, maintaining strict sequential order
**Validates: Requirements 1.1, 1.2**

**Property 3: Status transition validity**
*For any* session status change, the transition should follow valid business rules (pending→conducted/holiday/cancelled, holiday→conducted, but never conducted→pending)
**Validates: Requirements 2.1, 2.2, 2.3**

**Property 4: Holiday session preservation**
*For any* session marked as holiday, it should remain available for future conduct and not be skipped in the sequence
**Validates: Requirements 3.1, 3.3**

**Property 5: Cancelled session finality**
*For any* session marked as cancelled, it should be permanently removed from the sequence and never be available for conduct
**Validates: Requirements 3.2, 3.4**

**Property 6: Progress calculation accuracy**
*For any* class section, the completion percentage should equal (conducted + cancelled sessions) / 150 * 100
**Validates: Requirements 5.1, 5.4**

**Property 7: Sequence integrity maintenance**
*For any* bulk operation or data modification, the resulting session sequence should maintain completeness with no gaps between day 1 and day 150
**Validates: Requirements 6.2, 6.4**

**Property 8: Concurrent access consistency**
*For any* class section accessed by multiple facilitators simultaneously, all should see the same "today's session" and status information
**Validates: Requirements 2.5**

**Property 9: Attendance requirement enforcement**
*For any* session marked as conducted, an attendance record should be created and marked as completed before the session can be considered fully processed
**Validates: Requirements 2.4**

**Property 11: Automatic session generation completeness**
*For any* new class section created, the system should automatically generate exactly 150 planned sessions with sequential day numbers 1-150
**Validates: Requirements 7.1, 7.3**

**Property 12: Template application consistency**
*For any* session template applied to multiple classes, all target classes should receive identical session structures with appropriate customization for class-specific details
**Validates: Requirements 9.2, 9.4**

**Property 13: Bulk operation atomicity**
*For any* bulk operation that fails partially, the system should either complete all changes or rollback all changes, never leaving the system in an inconsistent state
**Validates: Requirements 8.4, 8.5**

**Property 14: Session deletion impact validation**
*For any* session deletion operation, the system should prevent deletion if it would create sequence gaps or orphan attendance records
**Validates: Requirements 8.2, 8.3**

**Property 15: Performance optimization effectiveness**
*For any* session management operation involving more than 100 sessions, the response time should not exceed 5 seconds for UI feedback
**Validates: Requirements 10.1, 10.4**

## Session Status Logic

### Status Definitions

**PENDING**: Session has not been processed yet
- Shows as "Today's Session" if it's the next in sequence
- Can transition to: CONDUCTED, HOLIDAY, CANCELLED

**CONDUCTED**: Session was completed with attendance
- Permanently completed, cannot be changed
- Moves sequence to next day
- Requires attendance records

**HOLIDAY**: Session was skipped due to holiday
- Can be conducted on any future date
- Does not advance sequence until conducted
- Can transition to: CONDUCTED

**CANCELLED**: Session was permanently cancelled
- Cannot be conducted in the future
- Advances sequence to next day immediately
- Permanent decision with logged reason

### Valid Cancellation Reasons

**When "Cancel Session" is REQUIRED** - These are real scenarios:

✅ **Valid Cancel Use-Cases:**
1. **School permanently shuts down** for that class
2. **Government removes a topic** from syllabus
3. **Exam period replaces class** permanently
4. **Duplicate / wrongly created** planned session
5. **Emergency** where session will never happen again

**Cancel Confirmation Process:**
```
1. Facilitator clicks "Cancel Session"
2. System shows dropdown with valid reasons
3. Facilitator must select specific reason
4. System shows impact warning: "This session will be permanently removed"
5. Facilitator confirms cancellation
6. System logs reason, timestamp, and user for audit
```

### Sequence Progression Logic

```python
def get_todays_session(class_section):
    """
    Returns the next session that should be shown as 'Today's Session'
    """
    # Find the first session that is not CONDUCTED or CANCELLED
    next_session = PlannedSession.objects.filter(
        class_section=class_section,
        is_active=True
    ).exclude(
        actual_sessions__status__in=['conducted', 'cancelled']
    ).order_by('day_number').first()
    
    return next_session
```

### Holiday vs Cancel Logic

**Holiday Scenario:**
```
Day 5 → Mark Holiday → Day 5 still pending, show Day 6 as today
Later: Can conduct Day 5 on any date
```

**Cancel Scenario:**
```
Day 5 → Select Cancel Reason → Confirm Impact → Day 5 permanently skipped
Day 5 never appears again, show Day 6 as today
```

## Error Handling

### Sequence Integrity Errors
- **Missing Sessions**: If days are missing from 1-150 sequence, auto-generate missing planned sessions
- **Duplicate Days**: If duplicate day numbers exist, merge or renumber to maintain sequence
- **Out of Order**: If sessions are processed out of order, maintain sequence but log warnings

### Status Transition Errors
- **Invalid Transitions**: Prevent invalid status changes (e.g., conducted → pending)
- **Missing Attendance**: Block session completion if attendance is not marked
- **Concurrent Updates**: Handle simultaneous status changes with optimistic locking

### Data Consistency Errors
- **Orphaned Sessions**: If actual sessions exist without planned sessions, create missing planned sessions
- **Progress Calculation**: If progress metrics are inconsistent, recalculate from actual data
- **Sequence Health**: If sequence health status is incorrect, run integrity check and update

## Testing Strategy

### Unit Testing Approach
Unit tests will verify specific functionality and edge cases:
- Session sequence calculation with various completion states
- Status transition validation with all possible combinations
- Progress calculation accuracy with different session distributions
- Holiday and cancel logic with edge cases
- Concurrent access handling with multiple users

### Property-Based Testing Approach
Property-based tests will verify universal behaviors using **pytest-hypothesis**:
- Each property-based test will run a minimum of 100 iterations
- Tests will generate random session states, class configurations, and user actions
- Each test will be tagged with: **Feature: session-sequence-management, Property {number}: {property_text}**

**Dual Testing Value**: Unit tests catch specific bugs and verify concrete examples, while property tests verify general correctness across all possible inputs, ensuring robust sequence management under all conditions.

### Integration Testing
- Test complete facilitator workflow from login to session completion
- Verify admin tools for sequence management and repair
- Test bulk operations and their impact on sequence integrity
- Validate reporting and analytics accuracy

### Performance Testing
- Test sequence calculation performance with large numbers of classes
- Measure database query efficiency for session lookups
- Verify system performance under concurrent facilitator access
- Benchmark bulk sequence operations and repairs

## Today's Session Complete Workflow

### Step-by-Step Facilitator Flow

**1. Session Overview (Left Side Card)**
```
┌─────────────────────────────────┐
│ Today's Session - Day 5         │
│ ─────────────────────────────── │
│ 📋 Lesson Plan Template         │
│ 📥 Download PDF                 │
│ 📤 Upload Completed Plan        │
│ ─────────────────────────────── │
│ ✅ Preparation Checklist        │
│ 🎁 Reward Students              │
│ 📝 Conduct Session              │
│ 💭 Session Feedback             │
└─────────────────────────────────┘
```

**2. Preparation Phase**
- Display day-wise preparation checklist
- Each checkpoint clickable with save functionality:
  - ☐ Lesson plan reviewed
  - ☐ Materials prepared  
  - ☐ Technology tested
  - ☐ Classroom setup ready
  - ☐ Student list reviewed
  - ☐ Previous feedback reviewed
- Progress saved to database with timestamps

**3. Lesson Plan Management**
- Download button for template PDF from `static/pdf/` folder
- Upload interface for completed lesson plan
- Submit button saves file with session date/day to database
- Display upload confirmation and file details

**4. Reward Phase**
- Reward button for student recognition
- Upload photo or text description of rewards given
- Save reward data with admin visibility
- Track which students received rewards

**5. Session Conduct Phase**
- Display full day-wise session content
- Integrated feedback form for real-time student analysis
- Student progression tracking during session
- Mark attendance functionality

**6. Session Feedback**
- During-session feedback card for student class analysis
- Student progression points input
- Final facilitator personal reflection (required)
- Submit feedback before session can be closed

**7. Session Completion**
- All feedback must be completed
- Session marked as conducted
- Automatic progression to next day
- Session closure with data persistence

### UI Layout Structure

```
┌─────────────────┬─────────────────────────────────────┐
│ Left Side Card  │ Main Content Area                   │
│                 │                                     │
│ 📋 Lesson Plan  │ [Current Step Content]             │
│ ✅ Preparation  │                                     │
│ 🎁 Rewards      │ • Preparation Checklist             │
│ 📝 Conduct      │ • Session Content                   │
│ 💭 Feedback     │ • Feedback Forms                    │
│                 │ • Completion Summary                │
│ [Progress Bar]  │                                     │
│                 │                                     │
│ [Next Step Btn] │ [Step-specific Actions]             │
└─────────────────┴─────────────────────────────────────┘
```