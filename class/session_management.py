"""
Session Sequence Management Logic
Implements the core business logic for 1-150 day session sequence management
"""

from django.db import models, transaction
from django.db.models import Q, Count, Max, Min
from django.utils import timezone
from django.core.exceptions import ValidationError
from typing import Optional, List, Dict, Any, Tuple
import logging

from .models import (
    PlannedSession, ActualSession, ClassSection, User,
    SessionBulkTemplate, CANCELLATION_REASONS
)

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result object for validation operations"""
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error: str):
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)


class ProgressMetrics:
    """Progress metrics for a class section"""
    def __init__(self, class_section: ClassSection):
        self.class_section = class_section
        self.total_sessions = 150
        self.conducted_sessions = 0
        self.cancelled_sessions = 0
        self.holiday_sessions = 0
        self.pending_sessions = 0
        self.completion_percentage = 0.0
        self.next_day_number = 1
        self.current_session = None


class SessionSequenceCalculator:
    """
    Determines the correct "today's session" for any class section
    Implements the core sequence calculation logic
    """
    
    @staticmethod
    def get_next_pending_session(class_section: ClassSection) -> Optional[PlannedSession]:
        """
        Returns the next session that needs to be conducted
        This is the core "Today's Session" logic
        
        IMPORTANT: Sessions should only advance to the next day after midnight,
        not immediately after conducting or marking as holiday
        """
        from django.utils import timezone
        today = timezone.now().date()
        
        try:
            # First, check if there's a session that was conducted or marked as holiday TODAY
            # If so, return that session (don't advance until tomorrow)
            todays_session = ActualSession.objects.filter(
                planned_session__class_section=class_section,
                date=today
            ).select_related('planned_session').first()
            
            if todays_session:
                # If there's a session for today, return that planned session
                # This ensures we don't advance to next day until tomorrow
                logger.info(f"Found today's session for {class_section}: Day {todays_session.planned_session.day_number} (Status: {todays_session.status})")
                return todays_session.planned_session
            
            # If no session for today, find the next session that hasn't been conducted or cancelled
            next_session = PlannedSession.objects.filter(
                class_section=class_section,
                is_active=True
            ).exclude(
                actual_sessions__status__in=['conducted', 'cancelled']
            ).order_by('day_number').first()
            
            # If no session found, check if we have any sessions at all
            if not next_session:
                total_sessions = PlannedSession.objects.filter(
                    class_section=class_section,
                    is_active=True
                ).count()
                
                if total_sessions == 0:
                    logger.warning(f"No planned sessions found for {class_section}")
                    return None
                
                # Check if all sessions are truly completed
                completed_count = ActualSession.objects.filter(
                    planned_session__class_section=class_section,
                    status__in=['conducted', 'cancelled']
                ).count()
                
                if completed_count >= total_sessions:
                    logger.info(f"All sessions completed for {class_section}")
                    return None
                
                # There might be sessions without actual sessions, get the first one
                next_session = PlannedSession.objects.filter(
                    class_section=class_section,
                    is_active=True
                ).order_by('day_number').first()
            
            logger.info(f"Next pending session for {class_section}: Day {next_session.day_number if next_session else 'None'}")
            return next_session
            
        except Exception as e:
            logger.error(f"Error getting next pending session for {class_section}: {e}")
            return None
    
    @staticmethod
    def validate_sequence_integrity(class_section: ClassSection) -> ValidationResult:
        """
        Checks for gaps or issues in the session sequence
        Validates that all days 1-150 are present and properly ordered
        """
        result = ValidationResult(True)
        
        try:
            # Get all planned sessions for this class
            planned_sessions = PlannedSession.objects.filter(
                class_section=class_section,
                is_active=True
            ).order_by('day_number')
            
            if not planned_sessions.exists():
                result.add_error("No planned sessions found for this class")
                return result
            
            # Check for complete 1-150 sequence
            day_numbers = list(planned_sessions.values_list('day_number', flat=True))
            expected_days = set(range(1, 151))  # 1-150
            actual_days = set(day_numbers)
            
            # Check for missing days
            missing_days = expected_days - actual_days
            if missing_days:
                missing_list = sorted(list(missing_days))
                result.add_error(f"Missing session days: {missing_list}")
            
            # Check for duplicate days
            if len(day_numbers) != len(set(day_numbers)):
                duplicates = [day for day in set(day_numbers) if day_numbers.count(day) > 1]
                result.add_error(f"Duplicate session days: {duplicates}")
            
            # Check for days outside 1-150 range
            invalid_days = [day for day in day_numbers if day < 1 or day > 150]
            if invalid_days:
                result.add_error(f"Invalid day numbers (must be 1-150): {invalid_days}")
            
            # Check sequence position consistency
            for session in planned_sessions:
                if session.sequence_position and session.sequence_position != session.day_number:
                    result.add_warning(f"Day {session.day_number} has inconsistent sequence_position: {session.sequence_position}")
            
            logger.info(f"Sequence integrity check for {class_section}: {result.is_valid}")
            
        except Exception as e:
            logger.error(f"Error validating sequence integrity for {class_section}: {e}")
            result.add_error(f"Validation error: {str(e)}")
        
        return result
    
    @staticmethod
    def calculate_progress(class_section: ClassSection) -> ProgressMetrics:
        """
        Computes completion percentage and metrics for a class section
        """
        metrics = ProgressMetrics(class_section)
        
        try:
            # Get all planned sessions
            planned_sessions = PlannedSession.objects.filter(
                class_section=class_section,
                is_active=True
            )
            
            metrics.total_sessions = planned_sessions.count()
            
            # Count sessions by status
            status_counts = ActualSession.objects.filter(
                planned_session__class_section=class_section
            ).values('status').annotate(count=Count('id'))
            
            for status_count in status_counts:
                status = status_count['status']
                count = status_count['count']
                
                if status == 'conducted':
                    metrics.conducted_sessions = count
                elif status == 'cancelled':
                    metrics.cancelled_sessions = count
                elif status == 'holiday':
                    metrics.holiday_sessions = count
            
            # Calculate pending sessions
            metrics.pending_sessions = metrics.total_sessions - (
                metrics.conducted_sessions + metrics.cancelled_sessions
            )
            
            # Calculate completion percentage (conducted + cancelled = completed)
            completed_sessions = metrics.conducted_sessions + metrics.cancelled_sessions
            if metrics.total_sessions > 0:
                metrics.completion_percentage = (completed_sessions / metrics.total_sessions) * 100
            
            # Get next session
            metrics.current_session = SessionSequenceCalculator.get_next_pending_session(class_section)
            if metrics.current_session:
                metrics.next_day_number = metrics.current_session.day_number
            else:
                # All sessions completed
                metrics.next_day_number = 151  # Beyond the sequence
            
            logger.info(f"Progress metrics for {class_section}: {metrics.completion_percentage}% complete")
            
        except Exception as e:
            logger.error(f"Error calculating progress for {class_section}: {e}")
        
        return metrics
    
    @staticmethod
    def get_session_history(class_section: ClassSection, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Returns session history with status information
        """
        try:
            # Get all actual sessions with their planned sessions
            actual_sessions = ActualSession.objects.filter(
                planned_session__class_section=class_section
            ).select_related('planned_session', 'facilitator').order_by('-date')[:limit]
            
            history = []
            for actual in actual_sessions:
                history.append({
                    'day_number': actual.planned_session.day_number,
                    'title': actual.planned_session.title,
                    'date': actual.date,
                    'status': actual.status,
                    'facilitator': actual.facilitator.full_name if actual.facilitator else 'Unknown',
                    'duration_minutes': actual.duration_minutes,
                    'attendance_marked': actual.attendance_marked,
                    'cancellation_reason': actual.get_cancellation_reason_display() if actual.cancellation_reason else None,
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting session history for {class_section}: {e}")
            return []


class SessionStatusManager:
    """
    Manages session status transitions and business rules
    Handles conduct, holiday, and cancellation logic
    """
    
    @staticmethod
    def conduct_session(planned_session: PlannedSession, facilitator: User, 
                       remarks: str = "", duration_minutes: int = None) -> ActualSession:
        """
        Marks session as conducted and creates attendance records
        """
        try:
            with transaction.atomic():
                # Create or update actual session
                actual_session, created = ActualSession.objects.get_or_create(
                    planned_session=planned_session,
                    date=timezone.now().date(),
                    defaults={
                        'facilitator': facilitator,
                        'status': 'conducted',
                        'remarks': remarks,
                        'conducted_at': timezone.now(),
                        'duration_minutes': duration_minutes,
                        'status_changed_by': facilitator,
                        'status_change_reason': 'Session conducted by facilitator'
                    }
                )
                
                if not created:
                    # Update existing session
                    actual_session.status = 'conducted'
                    actual_session.facilitator = facilitator
                    actual_session.remarks = remarks
                    actual_session.conducted_at = timezone.now()
                    actual_session.duration_minutes = duration_minutes
                    actual_session.status_changed_by = facilitator
                    actual_session.status_change_reason = 'Session conducted by facilitator'
                    actual_session.save()
                
                logger.info(f"Session conducted: {planned_session} by {facilitator}")
                return actual_session
                
        except Exception as e:
            logger.error(f"Error conducting session {planned_session}: {e}")
            raise ValidationError(f"Failed to conduct session: {str(e)}")
    
    @staticmethod
    def mark_holiday(planned_session: PlannedSession, facilitator: User, 
                    reason: str = "") -> ActualSession:
        """
        Marks session as holiday while preserving for future conduct
        """
        try:
            with transaction.atomic():
                actual_session, created = ActualSession.objects.get_or_create(
                    planned_session=planned_session,
                    date=timezone.now().date(),
                    defaults={
                        'facilitator': facilitator,
                        'status': 'holiday',
                        'remarks': reason,
                        'can_be_rescheduled': True,
                        'status_changed_by': facilitator,
                        'status_change_reason': f'Marked as holiday: {reason}'
                    }
                )
                
                if not created:
                    # Update existing session
                    actual_session.status = 'holiday'
                    actual_session.facilitator = facilitator
                    actual_session.remarks = reason
                    actual_session.can_be_rescheduled = True
                    actual_session.status_changed_by = facilitator
                    actual_session.status_change_reason = f'Marked as holiday: {reason}'
                    actual_session.save()
                
                logger.info(f"Session marked as holiday: {planned_session} by {facilitator}")
                return actual_session
                
        except Exception as e:
            logger.error(f"Error marking session as holiday {planned_session}: {e}")
            raise ValidationError(f"Failed to mark session as holiday: {str(e)}")
    
    @staticmethod
    def cancel_session(planned_session: PlannedSession, facilitator: User, 
                      cancellation_reason: str, remarks: str = "") -> ActualSession:
        """
        Permanently cancels session and moves to next day
        """
        # Validate cancellation reason
        valid_reasons = [choice[0] for choice in CANCELLATION_REASONS]
        if cancellation_reason not in valid_reasons:
            raise ValidationError(f"Invalid cancellation reason. Must be one of: {valid_reasons}")
        
        try:
            with transaction.atomic():
                actual_session, created = ActualSession.objects.get_or_create(
                    planned_session=planned_session,
                    date=timezone.now().date(),
                    defaults={
                        'facilitator': facilitator,
                        'status': 'cancelled',
                        'remarks': remarks,
                        'cancellation_reason': cancellation_reason,
                        'cancellation_category': cancellation_reason,
                        'is_permanent_cancellation': True,
                        'can_be_rescheduled': False,
                        'status_changed_by': facilitator,
                        'status_change_reason': f'Cancelled: {dict(CANCELLATION_REASONS)[cancellation_reason]}'
                    }
                )
                
                if not created:
                    # Update existing session
                    actual_session.status = 'cancelled'
                    actual_session.facilitator = facilitator
                    actual_session.remarks = remarks
                    actual_session.cancellation_reason = cancellation_reason
                    actual_session.cancellation_category = cancellation_reason
                    actual_session.is_permanent_cancellation = True
                    actual_session.can_be_rescheduled = False
                    actual_session.status_changed_by = facilitator
                    actual_session.status_change_reason = f'Cancelled: {dict(CANCELLATION_REASONS)[cancellation_reason]}'
                    actual_session.save()
                
                logger.info(f"Session cancelled: {planned_session} by {facilitator}, reason: {cancellation_reason}")
                return actual_session
                
        except Exception as e:
            logger.error(f"Error cancelling session {planned_session}: {e}")
            raise ValidationError(f"Failed to cancel session: {str(e)}")
    
    @staticmethod
    def validate_status_change(current_status: str, new_status: str) -> bool:
        """
        Ensures status transitions are valid according to business rules
        """
        valid_transitions = {
            'pending': ['conducted', 'holiday', 'cancelled'],
            'holiday': ['conducted'],  # Holiday sessions can be conducted later
            'conducted': [],  # Conducted sessions cannot be changed
            'cancelled': []   # Cancelled sessions cannot be changed
        }
        
        if current_status not in valid_transitions:
            return False
        
        return new_status in valid_transitions[current_status]


class SessionBulkManager:
    """
    Handles bulk operations on sessions across multiple classes
    """
    
    @staticmethod
    def generate_sessions_for_class(class_section: ClassSection, 
                                  template: SessionBulkTemplate = None,
                                  created_by: User = None) -> Dict[str, Any]:
        """
        Auto-creates 1-150 sessions for new class
        """
        result = {
            'success': False,
            'created_count': 0,
            'skipped_count': 0,
            'errors': [],
            'sessions_created': []
        }
        
        try:
            with transaction.atomic():
                # Check if sessions already exist
                existing_sessions = PlannedSession.objects.filter(
                    class_section=class_section,
                    is_active=True
                ).count()
                
                if existing_sessions > 0:
                    result['errors'].append(f"Class already has {existing_sessions} sessions")
                    return result
                
                # Generate 150 sessions
                sessions_to_create = []
                for day_number in range(1, 151):
                    # Use template if provided
                    title = f"Day {day_number}"
                    description = ""
                    
                    if template and template.day_templates:
                        day_template = template.day_templates.get(str(day_number), {})
                        title = day_template.get('title', title)
                        description = day_template.get('description', description)
                    
                    session = PlannedSession(
                        class_section=class_section,
                        day_number=day_number,
                        title=title,
                        description=description,
                        sequence_position=day_number,
                        is_required=True,
                        is_active=True
                    )
                    sessions_to_create.append(session)
                
                # Bulk create sessions
                created_sessions = PlannedSession.objects.bulk_create(sessions_to_create)
                result['created_count'] = len(created_sessions)
                result['success'] = True
                
                # Update template usage count
                if template:
                    template.usage_count += 1
                    template.save()
                
                logger.info(f"Generated {result['created_count']} sessions for {class_section}")
                
        except Exception as e:
            logger.error(f"Error generating sessions for {class_section}: {e}")
            result['errors'].append(str(e))
        
        return result
    
    @staticmethod
    def repair_sequence_gaps(class_section: ClassSection, created_by: User = None) -> Dict[str, Any]:
        """
        Fixes missing sessions in the 1-150 sequence
        """
        result = {
            'success': False,
            'created_count': 0,
            'errors': [],
            'gaps_filled': []
        }
        
        try:
            with transaction.atomic():
                # Get existing day numbers
                existing_days = set(
                    PlannedSession.objects.filter(
                        class_section=class_section,
                        is_active=True
                    ).values_list('day_number', flat=True)
                )
                
                # Find missing days
                all_days = set(range(1, 151))
                missing_days = all_days - existing_days
                
                if not missing_days:
                    result['success'] = True
                    return result
                
                # Create missing sessions
                sessions_to_create = []
                for day_number in sorted(missing_days):
                    session = PlannedSession(
                        class_section=class_section,
                        day_number=day_number,
                        title=f"Day {day_number}",
                        description="Auto-generated to fill sequence gap",
                        sequence_position=day_number,
                        is_required=True,
                        is_active=True
                    )
                    sessions_to_create.append(session)
                
                # Bulk create missing sessions
                created_sessions = PlannedSession.objects.bulk_create(sessions_to_create)
                result['created_count'] = len(created_sessions)
                result['gaps_filled'] = sorted(list(missing_days))
                result['success'] = True
                
                logger.info(f"Filled {result['created_count']} sequence gaps for {class_section}")
                
        except Exception as e:
            logger.error(f"Error repairing sequence gaps for {class_section}: {e}")
            result['errors'].append(str(e))
        
        return result