# Grouped Session Attendance UI Fix

## Issue
When facilitators conducted a grouped session and clicked the "Conduct Grouped Session" button, the attendance UI was not opening after task completion. The workflow was broken because:

1. Facilitator clicks "Conduct Grouped Session" button
2. System redirects to `facilitator_task_step` (task/preparation page)
3. Facilitator completes task and clicks "Complete & Continue to Conduct"
4. System was redirecting back to `start_session` instead of `mark_attendance`
5. This created a loop and the attendance UI never opened

## Root Cause
The `facilitator_task_complete` function in `class/facilitator_task_views.py` was redirecting to `start_session` instead of `mark_attendance`. This caused the workflow to loop back instead of proceeding to attendance marking.

## Solution

### 1. Updated `facilitator_task_complete` function
**File**: `class/facilitator_task_views.py`

Changed the redirect from:
```python
return redirect('start_session', planned_session_id=actual_session.planned_session.id)
```

To:
```python
return redirect('mark_attendance', actual_session_id=actual_session_id)
```

This ensures that after completing the task step, the facilitator is taken directly to the attendance marking page.

### 2. Updated facilitator task template
**File**: `Templates/facilitator/facilitator_task.html`

- Changed button text from "Complete & Continue to Conduct" to "Complete & Mark Attendance" for clarity
- Added a "Skip Task" button that allows facilitators to skip the task step and go directly to attendance marking
- This provides flexibility for facilitators who don't need to upload tasks

## Workflow After Fix

### For Grouped Sessions:
1. Facilitator clicks "🔗 Conduct Grouped Session (All X Classes)" button
2. System creates ActualSession for all grouped classes
3. System redirects to `facilitator_task_step` (task/preparation page)
4. Facilitator can:
   - Upload photos/videos/Facebook links (optional)
   - Click "Complete & Mark Attendance" to proceed to attendance marking
   - Click "Skip Task" to skip directly to attendance marking
5. System redirects to `mark_attendance` page
6. Facilitator marks attendance for ALL grouped classes at once
7. System saves attendance and redirects back to today's session page

### For Single Sessions:
- Same workflow applies, but only for one class

## Testing
The fix has been tested with:
- Grouped sessions with 2+ classes
- Single sessions
- Task completion with and without uploads
- Skip task functionality

## Files Modified
1. `class/facilitator_task_views.py` - Updated `facilitator_task_complete` function
2. `Templates/facilitator/facilitator_task.html` - Updated button text and added Skip Task button

## Status
✅ **FIXED** - Grouped session attendance UI now opens correctly after conducting a session
