# Design Document

## Overview

The Facilitator Student Management system extends the existing CLAS Django application to provide facilitators with comprehensive student management capabilities within their assigned schools. The solution leverages the existing Django models (User, School, ClassSection, Enrollment) and authentication system while adding new views, templates, and URL patterns specifically for facilitator-scoped student operations.

The design maintains the existing admin-style functionality but restricts access based on facilitator school assignments, ensuring data security and proper access control. The system integrates seamlessly with the current facilitator interface through sidebar navigation enhancements.

## Architecture

The system follows Django's Model-View-Template (MVT) architecture pattern with role-based access control:

### Presentation Layer
- **Facilitator Templates**: New HTML templates for school listing, class details, and student management
- **Sidebar Integration**: Enhanced facilitator sidebar with student management navigation
- **Form Components**: Student creation and editing forms with validation

### Business Logic Layer
- **Facilitator Views**: Django class-based views with permission decorators for school-scoped operations
- **Access Control**: Permission checking to ensure facilitators only access assigned schools
- **Student Operations**: CRUD operations for student records within facilitator scope

### Data Access Layer
- **Existing Models**: Leverages current User, School, ClassSection, Enrollment models
- **QuerySet Filtering**: School-based filtering for all student-related queries
- **Database Integrity**: Maintains referential integrity and audit trails

## Components and Interfaces

### FacilitatorStudentViews
**Purpose**: Handles all facilitator student management operations
**Key Views**:
- `FacilitatorSchoolListView`: Displays assigned schools
- `FacilitatorSchoolDetailView`: Shows classes within a school
- `FacilitatorStudentListView`: Lists students with filtering
- `FacilitatorStudentCreateView`: Creates new students
- `FacilitatorStudentUpdateView`: Edits existing students

**Interface**:
```python
class FacilitatorStudentViews:
    def get_assigned_schools(facilitator: User) -> QuerySet[School]
    def get_school_classes(school: School, facilitator: User) -> QuerySet[ClassSection]
    def get_students_in_scope(facilitator: User, filters: dict) -> QuerySet[User]
    def create_student(student_data: dict, facilitator: User) -> User
    def update_student(student: User, student_data: dict, facilitator: User) -> User
```

### AccessControlMixin
**Purpose**: Ensures facilitators only access assigned schools and their students
**Key Methods**:
- `check_school_access()`: Verifies facilitator assignment to school
- `filter_by_assigned_schools()`: Applies school-based filtering to querysets
- `get_facilitator_schools()`: Returns schools assigned to current facilitator

**Interface**:
```python
class AccessControlMixin:
    def check_school_access(self, school_id: int) -> bool
    def filter_by_assigned_schools(self, queryset: QuerySet) -> QuerySet
    def get_facilitator_schools(self) -> QuerySet[School]
```

### StudentFormHandler
**Purpose**: Manages student form creation, validation, and processing
**Key Methods**:
- `create_student_form()`: Generates form with school-scoped class choices
- `validate_student_data()`: Validates form data and business rules
- `process_student_form()`: Handles form submission and database updates

**Interface**:
```python
class StudentFormHandler:
    def create_student_form(facilitator: User) -> StudentForm
    def validate_student_data(form_data: dict) -> ValidationResult
    def process_student_form(form: StudentForm, facilitator: User) -> ProcessResult
```

## Data Models

### FacilitatorScope
Represents the scope of schools and classes accessible to a facilitator.

```python
class FacilitatorScope:
    facilitator: User              # The facilitator user
    assigned_schools: List[School] # Schools assigned to facilitator
    accessible_classes: List[ClassSection] # Classes within assigned schools
    student_count: int            # Total students in scope
```

### StudentManagementContext
Context data for student management operations.

```python
class StudentManagementContext:
    current_school: Optional[School]     # Currently selected school
    current_class: Optional[ClassSection] # Currently selected class
    available_filters: Dict[str, List]   # Available filter options
    student_list: List[User]            # Filtered student list
    pagination_info: PaginationData     # Pagination details
```

### StudentFormData
Data structure for student creation and editing forms.

```python
class StudentFormData:
    personal_info: Dict[str, str]       # Name, ID, contact details
    enrollment_info: Dict[str, Any]     # School, class, enrollment date
    academic_info: Dict[str, str]       # Grade level, academic status
    validation_errors: List[str]        # Form validation errors
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Before writing correctness properties, I need to analyze the acceptance criteria for testability:

### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated to eliminate redundancy:

- Properties 3.1, 3.4, and 7.2 all test the same core access control behavior (student filtering by assigned schools) and can be combined
- Properties 4.5 and 5.4 both test class assignment restrictions and are identical
- Properties 1.2, 2.2, and 3.2 all test information display completeness and can be grouped
- Properties 4.4 and 5.5 both test data integrity maintenance and can be combined

### Core Properties

**Property 1: School assignment access control**
*For any* facilitator and any school, the facilitator should only be able to access schools, classes, and students that belong to schools assigned to that facilitator
**Validates: Requirements 1.1, 2.5, 3.1, 3.4, 7.1, 7.2**

**Property 2: Information display completeness**
*For any* displayed entity (school, class, or student), all required information fields should be present in the rendered output according to the specification
**Validates: Requirements 1.2, 2.2, 3.2**

**Property 3: Alphabetical school ordering**
*For any* list of schools displayed to a facilitator, the schools should be ordered alphabetically by name
**Validates: Requirements 1.5**

**Property 4: Navigation link presence**
*For any* displayed entity that should have navigation links, the appropriate links should be present and functional
**Validates: Requirements 1.4, 2.3, 6.3**

**Property 5: Filtering functionality**
*For any* filter applied to class or student lists, the results should contain only items that match the filter criteria
**Validates: Requirements 2.4, 3.3, 3.5**

**Property 6: Form validation consistency**
*For any* student form submission with invalid data, the system should reject the submission and display appropriate validation errors
**Validates: Requirements 4.2, 5.3**

**Property 7: Student creation and enrollment**
*For any* new student created by a facilitator, the student should be automatically enrolled in the specified class and assigned a unique ID
**Validates: Requirements 4.3, 4.4**

**Property 8: Class assignment restrictions**
*For any* student creation or editing form, the available class options should be restricted to only classes within the facilitator's assigned schools
**Validates: Requirements 4.5, 5.4**

**Property 9: Form pre-population accuracy**
*For any* student selected for editing, the edit form should be pre-populated with the current student information exactly as stored in the database
**Validates: Requirements 5.1**

**Property 10: Data integrity maintenance**
*For any* student data modification, all related records (enrollments, counts) should be updated consistently and no orphaned records should be created
**Validates: Requirements 4.4, 5.5, 7.5**

**Property 11: Role-based navigation access**
*For any* user accessing the system, student management navigation options should only be visible to users with facilitator roles
**Validates: Requirements 6.5**

**Property 12: Audit logging completeness**
*For any* student management operation performed by a facilitator, the action should be logged with user identification and timestamp
**Validates: Requirements 7.3**

**Property 13: Unauthorized access handling**
*For any* attempt to access student data without proper authorization, the system should deny access and redirect appropriately
**Validates: Requirements 7.4**

**Property 14: Interface consistency**
*For any* form field or validation rule in the facilitator interface, it should match the equivalent functionality in the administrator interface
**Validates: Requirements 8.2, 8.5**

**Property 15: Bulk operation functionality**
*For any* bulk operation performed on multiple students, all selected students should be processed correctly and consistently
**Validates: Requirements 8.3**

## Error Handling

### Access Control Errors
- **Unauthorized School Access**: If a facilitator attempts to access a school not assigned to them, redirect to permission denied page
- **Invalid Student Access**: If a facilitator tries to access a student from an unassigned school, return 403 Forbidden
- **Role Verification Failure**: If user role cannot be verified, redirect to login page

### Form Processing Errors
- **Validation Failures**: Display field-specific error messages for invalid form data
- **Duplicate Student ID**: Generate alternative unique ID if collision occurs
- **Class Assignment Errors**: If selected class becomes unavailable, show error and refresh class options

### Data Integrity Errors
- **Enrollment Conflicts**: If student is already enrolled in target class, show appropriate message
- **Orphaned Records**: Implement cascade deletion and update procedures to maintain referential integrity
- **Concurrent Modifications**: Handle race conditions with optimistic locking and user notifications

## Testing Strategy

### Unit Testing Approach
Unit tests will verify specific functionality and edge cases:
- Form validation with various invalid inputs
- Access control with different user roles and school assignments
- Database operations and data integrity constraints
- Navigation and URL routing functionality
- Template rendering with different data scenarios

### Property-Based Testing Approach
Property-based tests will verify universal behaviors across all valid inputs using **pytest-hypothesis** library for Python:
- Each property-based test will run a minimum of 100 iterations
- Tests will generate random facilitator assignments, student data, and user interactions
- Each test will be tagged with the format: **Feature: facilitator-student-management, Property {number}: {property_text}**

**Dual Testing Value**: Unit tests catch specific bugs and verify concrete examples, while property tests verify general correctness across all possible inputs. Together they provide comprehensive coverage ensuring both specific functionality and universal behavior correctness.

### Integration Testing
- Test facilitator views within Django request/response cycle
- Verify database transactions and rollback behavior
- Test template rendering with various data combinations
- Validate form processing and redirect flows

### Security Testing
- Test access control with various user role combinations
- Verify data filtering prevents unauthorized access
- Test session management and authentication flows
- Validate audit logging captures all required information