# Facilitator Curriculum Integration Fix - Requirements

## Introduction

The facilitator's "Today's Session" page is incorrectly showing "All 150 sessions completed" when it should display the actual curriculum content for the current day. This happens because there's a disconnect between the admin-created curriculum sessions and the facilitator's planned sessions. The system needs to properly integrate curriculum content with the facilitator's daily session flow.

## Glossary

- **Facilitator**: A user who conducts daily sessions with students
- **Planned Session**: A session scheduled for a specific class on a specific day (1-150)
- **Curriculum Session**: Admin-created content for specific days and languages
- **Today's Session**: The current session a facilitator should conduct
- **Session Sequence**: The ordered progression of days 1-150 for each class
- **Class Section**: A specific class (e.g., UKG-A) in a school

## Requirements

### Requirement 1

**User Story:** As a facilitator, I want to see the actual curriculum content for today's session, so that I can conduct the class with the proper materials and activities.

#### Acceptance Criteria

1. WHEN a facilitator accesses their class's today session page, THE system SHALL display the curriculum content for the current day number
2. WHEN no planned sessions exist for a class, THE system SHALL automatically generate the 1-150 session sequence
3. WHEN curriculum content exists for the current day and language, THE system SHALL display the admin-managed content
4. WHEN no curriculum content exists for the current day, THE system SHALL display the static curriculum file content
5. WHEN a class has completed all 150 sessions, THE system SHALL display the completion message

### Requirement 2

**User Story:** As a facilitator, I want the system to automatically initialize my class sessions, so that I don't see confusing completion messages when starting a new class.

#### Acceptance Criteria

1. WHEN a facilitator first accesses a class that has no planned sessions, THE system SHALL automatically create sessions for days 1-150
2. WHEN sessions are auto-generated, THE system SHALL set the first session (Day 1) as the current pending session
3. WHEN auto-generation occurs, THE system SHALL log the creation for audit purposes
4. WHEN auto-generation fails, THE system SHALL display an error message with retry options
5. WHEN a class already has some sessions but not all 150, THE system SHALL fill in the missing gaps

### Requirement 3

**User Story:** As a facilitator, I want to see the correct day progression, so that I can follow the curriculum sequence properly.

#### Acceptance Criteria

1. WHEN a facilitator completes a session, THE system SHALL advance to the next day in sequence
2. WHEN a session is marked as holiday, THE system SHALL keep the same day for the next session
3. WHEN a session is cancelled, THE system SHALL advance to the next day in sequence
4. WHEN determining the current day, THE system SHALL use the lowest day number that hasn't been conducted or cancelled
5. WHEN all sessions are truly completed (conducted or cancelled), THE system SHALL display the completion message

### Requirement 4

**User Story:** As a facilitator, I want the curriculum content to match my class language preference, so that I can teach in the appropriate language.

#### Acceptance Criteria

1. WHEN a class has a language preference set, THE system SHALL default to that language's curriculum
2. WHEN no language preference is set, THE system SHALL default to English curriculum
3. WHEN a facilitator switches languages, THE system SHALL load the corresponding curriculum content
4. WHEN curriculum content doesn't exist in the selected language, THE system SHALL fall back to the default language
5. WHEN falling back to default language, THE system SHALL notify the facilitator of the language change

### Requirement 5

**User Story:** As an admin, I want curriculum sessions to automatically integrate with facilitator sessions, so that content management is seamless.

#### Acceptance Criteria

1. WHEN an admin creates a curriculum session for a specific day, THE system SHALL make it available to all classes using that language
2. WHEN curriculum content is updated, THE system SHALL reflect changes immediately in facilitator sessions
3. WHEN curriculum content is deleted, THE system SHALL fall back to static content for that day
4. WHEN multiple curriculum versions exist for the same day, THE system SHALL use the most recent published version
5. WHEN curriculum content has school/class targeting, THE system SHALL only show it to the specified classes