"""
Django signals for automatic session generation
Handles automatic creation of 1-150 sessions when new classes are created
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import logging

from .models import ClassSection, PlannedSession, SessionBulkTemplate
from .session_management import SessionBulkManager

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=ClassSection)
def auto_generate_sessions_for_new_class(sender, instance, created, **kwargs):
    """
    Automatically generate 1-150 sessions when a new class is created
    """
    if created:  # Only for newly created classes
        try:
            logger.info(f"Auto-generating sessions for new class: {instance}")
            
            # Check if sessions already exist (safety check)
            existing_sessions = PlannedSession.objects.filter(
                class_section=instance,
                is_active=True
            ).count()
            
            if existing_sessions > 0:
                logger.warning(f"Class {instance} already has {existing_sessions} sessions, skipping auto-generation")
                return
            
            # Try to get a default template
            default_template = SessionBulkTemplate.objects.filter(
                is_active=True,
                language='english'  # Default to English
            ).first()
            
            # Generate sessions using SessionBulkManager
            result = SessionBulkManager.generate_sessions_for_class(
                class_section=instance,
                template=default_template,
                created_by=None  # System generated
            )
            
            if result['success']:
                logger.info(f"Successfully auto-generated {result['created_count']} sessions for {instance}")
            else:
                logger.error(f"Failed to auto-generate sessions for {instance}: {result['errors']}")
                
        except Exception as e:
            logger.error(f"Error in auto-generating sessions for {instance}: {e}")


@receiver(post_save, sender=SessionBulkTemplate)
def update_template_usage_stats(sender, instance, created, **kwargs):
    """
    Update template statistics when templates are used
    """
    if not created:  # Only for updates, not new creations
        logger.info(f"Template {instance.name} usage updated")