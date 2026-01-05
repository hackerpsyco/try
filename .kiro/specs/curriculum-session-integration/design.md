# Design Document

## Overview

The Curriculum Session Integration system bridges the gap between admin-managed curriculum sessions and facilitator daily session interfaces. Currently, the system has two disconnected components: PlannedSession (class-specific sessions) and CurriculumSession (master curriculum content), with facilitators loading curriculum content from static HTML files. This integration creates a unified system where admin curriculum updates immediately reflect in facilitator Today Session views while maintaining backward compatibility with existing functionality.

The design leverages the existing Django architecture and models, adding integration layers that connect the admin curriculum management system with the facilitator session workflow without disrupting current operations.

## Architecture

The system follows a layered integration approach that connects existing components:

### Integration Layer
- **Content Resolution Service**: Determines whether to load admin-managed or static curriculum content
- **Session Synchronization**: Links PlannedSession instances with appropriate CurriculumSession content
- **Real-time Update Propagation**: Ensures curriculum changes immediately appear in facilitator views

### Enhanced Presentation Layer
- **Unified Today Session View**: Combines PlannedSession data with CurriculumSession content
- **Enhanced Class Sessions Interface**: Shows curriculum content source indicators and management options
- **Admin Curriculum Management**: Extended with class impact analysis and facilitator notification features

### Data Integration Layer
- **Content Source Resolution**: Intelligent routing between admin-managed and static content
- **Usage Tracking**: Logs curriculum access for analytics and impact analysis
- **Cache Management**: Optimized caching strategy for both content types

## Components and Interfaces

### CurriculumContentResolver
**Purpose**: Determines and loads appropriate curriculum content for facilitator views
**Key Methods**:
- `resolve_content()`: Determines whether to use admin-managed or static content
- `load_curriculum_content()`: Loads content from appropriate source with fallback
- `check_content_availability()`: Validates content availability for specific day/language
- `get_content_metadata()`: Returns information about content source and last update

**Interface**:
```python
class CurriculumContentResolver:
    def resolve_content(day: int, language: str, class_section: ClassSection) -> ContentResult
    def load_curriculum_content(day: int, language: str) -> str
    def check_content_availability(day: int, language: str) -> AvailabilityStatus
    def get_content_metadata(day: int, language: str) -> ContentMetadata
```

### SessionIntegrationService
**Purpose**: Manages the connection between PlannedSessions and CurriculumSessions
**Key Methods**:
- `link_planned_to_curriculum()`: Creates logical links between session types
- `get_integrated_session_data()`: Combines data from both session types
- `update_session_relationships()`: Maintains consistency between related sessions
- `validate_session_alignment()`: Checks for schedule mismatches

**Interface**:
```python
class SessionIntegrationService:
    def link_planned_to_curriculum(planned_session: PlannedSession) -> CurriculumSession
    def get_integrated_session_data(planned_session: PlannedSession) -> IntegratedSessionData
    def update_session_relationships(curriculum_session: CurriculumSession) -> List[PlannedSession]
    def validate_session_alignment(class_section: ClassSection) -> AlignmentReport
```

### UsageTrackingService
**Purpose**: Tracks curriculum access and provides analytics for admin decision-making
**Key Methods**:
- `log_curriculum_access()`: Records facilitator access to curriculum content
- `generate_usage_analytics()`: Creates reports on content usage patterns
- `get_impact_analysis()`: Analyzes potential impact of curriculum changes
- `track_content_effectiveness()`: Measures content engagement and success

**Interface**:
```python
class UsageTrackingService:
    def log_curriculum_access(session: CurriculumSession, facilitator: User, context: dict) -> UsageLog
    def generate_usage_analytics(filters: dict) -> AnalyticsReport
    def get_impact_analysis(curriculum_session: CurriculumSession) -> ImpactAnalysis
    def track_content_effectiveness(session: CurriculumSession) -> EffectivenessMetrics
```

### NotificationService
**Purpose**: Manages notifications to facilitators about curriculum changes
**Key Methods**:
- `notify_curriculum_update()`: Sends notifications about content changes
- `get_affected_facilitators()`: Identifies facilitators impacted by changes
- `create_update_summary()`: Generates summaries of curriculum changes
- `manage_notification_preferences()`: Handles facilitator notification settings

**Interface**:
```python
class NotificationService:
    def notify_curriculum_update(curriculum_session: CurriculumSession, change_type: str) -> NotificationResult
    def get_affected_facilitators(curriculum_session: CurriculumSession) -> List[User]
    def create_update_summary(changes: List[CurriculumChange]) -> UpdateSummary
    def manage_notification_preferences(facilitator: User, preferences: dict) -> bool
```

## Data Models

### Enhanced CurriculumSession
Extends the existing CurriculumSession model with integration-specific fields:

```python
class CurriculumSession(models.Model):
    # Existing fields...
    
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
```

### CurriculumUsageLog
Tracks facilitator access to curriculum content for analytics:

```python
class CurriculumUsageLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    curriculum_session = models.ForeignKey(
        CurriculumSession,
        on_delete=models.CASCADE,
        related_name='usage_logs'
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
```

### SessionContentMapping
Links PlannedSessions with their corresponding CurriculumSessions:

```python
class SessionContentMapping(models.Model):
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
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated to eliminate redundancy:

- Properties for content loading (1.1, 4.1, 4.3) can be combined into a comprehensive content resolution property
- Properties for real-time updates (1.2, 2.2) can be merged into a single update propagation property
- Properties for fallback behavior (1.4, 2.3, 4.5, 6.4) can be consolidated into a unified fallback property
- Properties for UI indicators (2.5, 8.1, 8.5) can be combined into a single indicator accuracy property
- Properties for analytics and tracking (3.3, 3.4, 7.4) can be merged into a comprehensive analytics property

### Core Properties

**Property 1: Content Resolution Accuracy**
*For any* facilitator Today Session access with specific day number and language, the system should load admin-managed CurriculumSession content when available, or fall back to static content when not available, with correct language matching
**Validates: Requirements 1.1, 1.4, 1.5, 4.1, 4.3**

**Property 2: Real-time Update Propagation**
*For any* CurriculumSession update by an admin, all active facilitator Today Session views displaying that day and language should immediately reflect the changes without requiring page refresh
**Validates: Requirements 1.2, 2.2**

**Property 3: Content Preservation Integrity**
*For any* curriculum content display, all formatting, links, multimedia elements, and structural components should be preserved exactly as they exist in the source (admin-managed or static)
**Validates: Requirements 1.3, 2.4, 5.3**

**Property 4: Unified Fallback Behavior**
*For any* scenario where admin-managed content is unavailable, deleted, or inaccessible, the system should gracefully fall back to static content with appropriate messaging and maintain all existing functionality
**Validates: Requirements 1.4, 2.3, 4.5, 6.4**

**Property 5: Session Integration Consistency**
*For any* Today Session display, PlannedSession data and CurriculumSession content should be properly combined while maintaining all existing workflow features and functionality
**Validates: Requirements 4.1, 4.2, 6.2**

**Property 6: Content Source Indicators**
*For any* admin interface displaying curriculum sessions or class sessions, indicators should correctly show whether content comes from admin-managed sessions or static files
**Validates: Requirements 2.5, 8.1, 8.5**

**Property 7: Automatic Session Linking**
*For any* PlannedSession creation or modification, the system should automatically establish correct relationships with corresponding CurriculumSessions based on day number and language
**Validates: Requirements 8.4, 9.5**

**Property 8: Impact Analysis Accuracy**
*For any* CurriculumSession being viewed or edited, the system should correctly identify and display all affected classes, facilitators, and active sessions
**Validates: Requirements 3.1, 3.2, 9.1, 9.2**

**Property 9: Usage Tracking Completeness**
*For any* facilitator access to curriculum content, a complete usage log should be created with accurate timestamp, user identification, content source, and session context
**Validates: Requirements 3.3, 7.5**

**Property 10: Analytics Generation Accuracy**
*For any* collection of usage logs and curriculum access data, the system should generate accurate analytics showing access frequency, popular content, usage patterns, and effectiveness metrics
**Validates: Requirements 3.4, 7.4**

**Property 11: Bulk Operation Reliability**
*For any* bulk import or management operation, the system should provide accurate progress indicators, detailed reporting, and proper conflict resolution while maintaining data integrity
**Validates: Requirements 5.1, 5.2, 5.4**

**Property 12: Content Availability Propagation**
*For any* curriculum content import or creation, the content should immediately become available to all relevant facilitators without requiring system restart or cache clearing
**Validates: Requirements 2.1, 5.5**

**Property 13: Backward Compatibility Preservation**
*For any* existing PlannedSession functionality, database schema, or facilitator workflow, the integration should maintain complete compatibility without breaking existing operations
**Validates: Requirements 6.1, 6.2, 6.3**

**Property 14: Performance Maintenance**
*For any* Today Session loading operation, the system should maintain or improve current loading times despite the additional curriculum integration functionality
**Validates: Requirements 6.5**

**Property 15: Template Management Consistency**
*For any* curriculum session template operation (creation, application, update), the system should maintain version history, track usage statistics, and provide proper customization options
**Validates: Requirements 7.1, 7.2, 7.3, 7.5**

**Property 16: Schedule Alignment Detection**
*For any* class section with PlannedSessions, the system should correctly identify and indicate mismatches between class progress and available curriculum content
**Validates: Requirements 9.3, 9.5**

**Property 17: Notification System Reliability**
*For any* curriculum update affecting active facilitator sessions, the system should provide appropriate notification options and accurately identify affected users
**Validates: Requirements 9.4**

## Error Handling

### Content Resolution Errors
- **Missing Curriculum Content**: When admin-managed content is not available, gracefully fall back to static content with clear messaging
- **Content Loading Failures**: If both admin-managed and static content fail to load, display error message with retry options
- **Language Mismatch**: If requested language content is not available, fall back to default language with notification

### Integration Synchronization Errors
- **Session Mapping Failures**: If PlannedSession cannot be linked to CurriculumSession, log error and continue with static content
- **Real-time Update Failures**: If curriculum updates cannot propagate to facilitator views, queue updates for retry
- **Data Consistency Issues**: If session data becomes inconsistent, provide admin tools to resolve conflicts

### Performance and Caching Errors
- **Cache Invalidation Failures**: If curriculum content cache cannot be updated, force cache refresh on next access
- **Database Connection Issues**: Implement connection pooling and retry logic for database operations
- **Concurrent Access Conflicts**: Handle multiple simultaneous updates to curriculum content with proper locking

### User Experience Errors
- **Permission Denied**: Provide clear error messages when users lack permissions for curriculum operations
- **Session Timeout**: Gracefully handle session timeouts during long curriculum operations
- **Browser Compatibility**: Ensure fallback functionality for older browsers or JavaScript disabled scenarios

## Testing Strategy

### Unit Testing Approach
Unit tests will verify specific integration functionality and edge cases:
- Content resolution logic with various availability scenarios
- Session mapping creation and maintenance
- Usage logging accuracy and completeness
- Template application and customization
- Error handling and fallback mechanisms

### Property-Based Testing Approach
Property-based tests will verify universal behaviors across all valid inputs using **pytest-hypothesis** library for Python:
- Each property-based test will run a minimum of 100 iterations
- Tests will generate random day numbers, languages, session data, and user interactions
- Each test will be tagged with the format: **Feature: curriculum-session-integration, Property {number}: {property_text}**

**Dual Testing Value**: Unit tests catch specific integration bugs and verify concrete examples, while property tests verify general correctness across all possible curriculum content and session combinations. Together they provide comprehensive coverage ensuring both specific functionality and universal behavior correctness.

### Integration Testing
- Test complete workflow from admin curriculum update to facilitator view display
- Verify database transaction integrity during bulk operations
- Test real-time update propagation across multiple concurrent users
- Validate backward compatibility with existing PlannedSession operations

### Performance Testing
- Measure Today Session loading times with curriculum integration
- Test system performance under high concurrent curriculum access
- Benchmark bulk import operations with large curriculum datasets
- Verify cache effectiveness and invalidation performance