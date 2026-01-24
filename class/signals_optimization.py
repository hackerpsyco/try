# Cache Invalidation Signals
# Automatically invalidates cache when data changes
# NO DATA CHANGES - Only cache management

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

# Import models
from .models import (
    ActualSession, Attendance, PlannedSession, 
    ClassSection, School, Enrollment
)

# =====================================================
# CACHE INVALIDATION ON DATA CHANGES
# =====================================================

@receiver(post_save, sender=ActualSession)
@receiver(post_delete, sender=ActualSession)
def invalidate_session_cache(sender, instance, **kwargs):
    """
    Invalidate cache when ActualSession changes
    
    NO DATA CHANGES - Only cache invalidation
    """
    try:
        # Invalidate all dashboards
        cache.delete('dashboard_stats_ADMIN')
        cache.delete('dashboard_stats_FACILITATOR')
        cache.delete('dashboard_stats_SUPERVISOR')
        
        # Invalidate specific class cache
        cache.delete(f'class_{instance.planned_session.class_section.id}_sessions')
        
        logger.info(f"Invalidated cache for ActualSession {instance.id}")
    except Exception as e:
        logger.error(f"Error invalidating session cache: {e}")


@receiver(post_save, sender=Attendance)
@receiver(post_delete, sender=Attendance)
def invalidate_attendance_cache(sender, instance, **kwargs):
    """
    Invalidate cache when Attendance changes
    
    NO DATA CHANGES - Only cache invalidation
    """
    try:
        # Invalidate all dashboards
        cache.delete('dashboard_stats_ADMIN')
        cache.delete('dashboard_stats_FACILITATOR')
        cache.delete('dashboard_stats_SUPERVISOR')
        
        # Invalidate specific session cache
        cache.delete(f'session_{instance.actual_session.id}_attendance')
        
        logger.info(f"Invalidated cache for Attendance {instance.id}")
    except Exception as e:
        logger.error(f"Error invalidating attendance cache: {e}")


@receiver(post_save, sender=PlannedSession)
@receiver(post_delete, sender=PlannedSession)
def invalidate_planned_session_cache(sender, instance, **kwargs):
    """
    Invalidate cache when PlannedSession changes
    
    NO DATA CHANGES - Only cache invalidation
    """
    try:
        # Invalidate all dashboards
        cache.delete('dashboard_stats_ADMIN')
        cache.delete('dashboard_stats_FACILITATOR')
        cache.delete('dashboard_stats_SUPERVISOR')
        
        # Invalidate specific class cache
        cache.delete(f'class_{instance.class_section.id}_sessions')
        
        logger.info(f"Invalidated cache for PlannedSession {instance.id}")
    except Exception as e:
        logger.error(f"Error invalidating planned session cache: {e}")


@receiver(post_save, sender=ClassSection)
@receiver(post_delete, sender=ClassSection)
def invalidate_class_cache(sender, instance, **kwargs):
    """
    Invalidate cache when ClassSection changes
    
    NO DATA CHANGES - Only cache invalidation
    """
    try:
        # Invalidate all dashboards
        cache.delete('dashboard_stats_ADMIN')
        cache.delete('dashboard_stats_FACILITATOR')
        cache.delete('dashboard_stats_SUPERVISOR')
        
        # Invalidate specific school cache
        cache.delete(f'school_{instance.school.id}_classes')
        
        logger.info(f"Invalidated cache for ClassSection {instance.id}")
    except Exception as e:
        logger.error(f"Error invalidating class cache: {e}")


@receiver(post_save, sender=School)
@receiver(post_delete, sender=School)
def invalidate_school_cache(sender, instance, **kwargs):
    """
    Invalidate cache when School changes
    
    NO DATA CHANGES - Only cache invalidation
    """
    try:
        # Invalidate all dashboards
        cache.delete('dashboard_stats_ADMIN')
        cache.delete('dashboard_stats_FACILITATOR')
        cache.delete('dashboard_stats_SUPERVISOR')
        
        logger.info(f"Invalidated cache for School {instance.id}")
    except Exception as e:
        logger.error(f"Error invalidating school cache: {e}")


@receiver(post_save, sender=Enrollment)
@receiver(post_delete, sender=Enrollment)
def invalidate_enrollment_cache(sender, instance, **kwargs):
    """
    Invalidate cache when Enrollment changes
    
    NO DATA CHANGES - Only cache invalidation
    """
    try:
        # Invalidate all dashboards
        cache.delete('dashboard_stats_ADMIN')
        cache.delete('dashboard_stats_FACILITATOR')
        cache.delete('dashboard_stats_SUPERVISOR')
        
        # Invalidate specific class cache
        cache.delete(f'class_{instance.class_section.id}_students')
        
        logger.info(f"Invalidated cache for Enrollment {instance.id}")
    except Exception as e:
        logger.error(f"Error invalidating enrollment cache: {e}")
