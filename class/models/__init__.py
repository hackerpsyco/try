from .users import User
from .users import Role
from .school import School  # ✅ THIS LINE FIXES YOUR ERROR
from .class_section import ClassSection
from .facilitor_school import FacilitatorSchool
from .students import (
    Student, Enrollment, PlannedSession, ActualSession, Attendance, SessionStep,
    SessionBulkTemplate, LessonPlanUpload, SessionReward, SessionFeedback, 
    SessionPreparationChecklist, StudentFeedback, TeacherFeedback, FeedbackAnalytics, CANCELLATION_REASONS
)
from .curriculum_sessions import (
    CurriculumSession, SessionTemplate, SessionUsageLog, ImportHistory, 
    SessionVersionHistory, CurriculumUsageLog, SessionContentMapping
)
from .calendar import (
    SupervisorCalendar, CalendarDate, OfficeWorkAttendance
)
from .facilitator_task import FacilitatorTask
from .student_performance import (
    Subject, PerformanceCutoff, StudentPerformance, StudentPerformanceSummary
)

