# Requirements Document

## Introduction

The facilitator attendance filtering functionality is currently broken due to a FieldError where the code attempts to reference 'actual_session' field on the ActualSession model itself, rather than using the correct field name 'date'. This prevents facilitators from accessing the attendance filtering interface, which is a critical feature for tracking student attendance.

## Glossary

- **ActualSession**: A model representing a conducted class session with a specific date
- **Attendance**: A model representing individual student attendance records linked to an ActualSession
- **Facilitator**: A user role that conducts classes and marks attendance
- **Date Filter**: A mechanism to filter sessions and attendance records by date ranges

## Requirements

### Requirement 1

**User Story:** As a facilitator, I want to access the attendance filtering interface, so that I can view and analyze student attendance data.

#### Acceptance Criteria

1. WHEN a facilitator accesses the attendance URL THEN the system SHALL load the attendance filtering interface without errors
2. WHEN the system applies date filters to ActualSession queries THEN the system SHALL use the correct field name 'date' instead of 'actual_session__date'
3. WHEN the system applies date filters to Attendance queries THEN the system SHALL use the correct field name 'actual_session__date'
4. WHEN date filtering is applied THEN the system SHALL return accurate results for the specified date range
5. WHEN no date filter is specified THEN the system SHALL display all available attendance data

### Requirement 2

**User Story:** As a facilitator, I want to filter attendance data by different time periods, so that I can analyze attendance patterns over specific timeframes.

#### Acceptance Criteria

1. WHEN a facilitator selects "today" period THEN the system SHALL filter sessions and attendance for the current date
2. WHEN a facilitator selects "this week" period THEN the system SHALL filter sessions and attendance for the current week
3. WHEN a facilitator selects "last week" period THEN the system SHALL filter sessions and attendance for the previous week
4. WHEN a facilitator selects "this month" period THEN the system SHALL filter sessions and attendance for the current month
5. WHEN a facilitator selects "last month" period THEN the system SHALL filter sessions and attendance for the previous month
6. WHEN a facilitator selects "custom" period with valid dates THEN the system SHALL filter sessions and attendance for the specified date range

### Requirement 3

**User Story:** As a facilitator, I want to see accurate attendance statistics, so that I can make informed decisions about student progress and engagement.

#### Acceptance Criteria

1. WHEN attendance statistics are calculated THEN the system SHALL use the correct field relationships between models
2. WHEN date filters are applied to statistics THEN the system SHALL maintain data consistency across all queries
3. WHEN displaying recent sessions THEN the system SHALL show accurate attendance counts for each session
4. WHEN calculating attendance percentages THEN the system SHALL use the filtered session count as the denominator
5. WHEN no sessions exist for the filtered period THEN the system SHALL display appropriate zero values without errors