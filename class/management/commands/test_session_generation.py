"""
Management command to test session generation functionality
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from ...models import School, ClassSection, PlannedSession, SessionBulkTemplate
from ...session_management import SessionBulkManager, SessionSequenceCalculator


class Command(BaseCommand):
    help = 'Test session generation functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-name',
            type=str,
            default='Test School',
            help='Name of the test school to create'
        )
        parser.add_argument(
            '--class-level',
            type=str,
            default='5',
            help='Class level for the test class'
        )
        parser.add_argument(
            '--section',
            type=str,
            default='A',
            help='Section for the test class'
        )

    def handle(self, *args, **options):
        school_name = options['school_name']
        class_level = options['class_level']
        section = options['section']
        
        self.stdout.write(
            self.style.SUCCESS(f'Testing session generation for {class_level}-{section} at {school_name}')
        )
        
        try:
            with transaction.atomic():
                # Create or get test school
                school, created = School.objects.get_or_create(
                    name=school_name,
                    defaults={
                        'udise': f'TEST{school_name.replace(" ", "")}001',
                        'block': 'Test Block',
                        'district': 'Test District',
                        'status': 1
                    }
                )
                
                if created:
                    self.stdout.write(f'Created test school: {school.name}')
                else:
                    self.stdout.write(f'Using existing school: {school.name}')
                
                # Create test class section
                class_section, created = ClassSection.objects.get_or_create(
                    school=school,
                    class_level=class_level,
                    section=section,
                    defaults={
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(f'Created test class: {class_section}')
                    
                    # The signal should automatically generate sessions
                    # Let's wait a moment and check
                    import time
                    time.sleep(1)
                    
                    # Check if sessions were generated
                    session_count = PlannedSession.objects.filter(
                        class_section=class_section,
                        is_active=True
                    ).count()
                    
                    self.stdout.write(f'Sessions automatically generated: {session_count}')
                    
                    if session_count == 150:
                        self.stdout.write(
                            self.style.SUCCESS('✅ Automatic session generation successful!')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️ Expected 150 sessions, got {session_count}')
                        )
                        
                        # Try manual generation
                        self.stdout.write('Attempting manual session generation...')
                        result = SessionBulkManager.generate_sessions_for_class(class_section)
                        
                        if result['success']:
                            self.stdout.write(
                                self.style.SUCCESS(f'✅ Manual generation successful: {result["created_count"]} sessions')
                            )
                        else:
                            self.stdout.write(
                                self.style.ERROR(f'❌ Manual generation failed: {result["errors"]}')
                            )
                    
                    # Test sequence integrity
                    self.stdout.write('Testing sequence integrity...')
                    validation_result = SessionSequenceCalculator.validate_sequence_integrity(class_section)
                    
                    if validation_result.is_valid:
                        self.stdout.write(
                            self.style.SUCCESS('✅ Sequence integrity check passed!')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Sequence integrity issues: {validation_result.errors}')
                        )
                    
                    # Test progress calculation
                    self.stdout.write('Testing progress calculation...')
                    progress_metrics = SessionSequenceCalculator.calculate_progress(class_section)
                    
                    self.stdout.write(f'Progress metrics:')
                    self.stdout.write(f'  Total sessions: {progress_metrics.total_sessions}')
                    self.stdout.write(f'  Conducted: {progress_metrics.conducted_sessions}')
                    self.stdout.write(f'  Cancelled: {progress_metrics.cancelled_sessions}')
                    self.stdout.write(f'  Pending: {progress_metrics.pending_sessions}')
                    self.stdout.write(f'  Completion: {progress_metrics.completion_percentage:.1f}%')
                    self.stdout.write(f'  Next day: {progress_metrics.next_day_number}')
                    
                    # Test next session calculation
                    next_session = SessionSequenceCalculator.get_next_pending_session(class_section)
                    if next_session:
                        self.stdout.write(f'Next pending session: Day {next_session.day_number}')
                    else:
                        self.stdout.write('No pending sessions found')
                    
                else:
                    self.stdout.write(f'Class already exists: {class_section}')
                    
                    # Check existing sessions
                    session_count = PlannedSession.objects.filter(
                        class_section=class_section,
                        is_active=True
                    ).count()
                    self.stdout.write(f'Existing sessions: {session_count}')
                
                self.stdout.write(
                    self.style.SUCCESS('Session generation test completed successfully!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Test failed with error: {str(e)}')
            )
            raise