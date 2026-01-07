"""
Management command to test session timeout functionality
"""

from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Test session timeout functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of user to test session timeout for',
        )
        parser.add_argument(
            '--expire-all',
            action='store_true',
            help='Expire all active sessions',
        )
        parser.add_argument(
            '--list-sessions',
            action='store_true',
            help='List all active sessions',
        )

    def handle(self, *args, **options):
        if options['list_sessions']:
            self.list_active_sessions()
        elif options['expire_all']:
            self.expire_all_sessions()
        elif options['user_email']:
            self.expire_user_sessions(options['user_email'])
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --list-sessions, --expire-all, or --user-email')
            )

    def list_active_sessions(self):
        """List all active sessions"""
        sessions = Session.objects.filter(expire_date__gt=timezone.now())
        
        self.stdout.write(f"Found {sessions.count()} active sessions:")
        
        for session in sessions:
            session_data = session.get_decoded()
            user_id = session_data.get('_auth_user_id')
            
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    user_info = f"{user.email} ({user.role.name})"
                except User.DoesNotExist:
                    user_info = f"User ID {user_id} (not found)"
            else:
                user_info = "Anonymous"
            
            last_activity = session_data.get('last_activity')
            if last_activity:
                last_activity_time = timezone.datetime.fromtimestamp(last_activity, tz=timezone.utc)
                time_since = timezone.now() - last_activity_time
                activity_info = f"Last activity: {time_since.total_seconds():.0f}s ago"
            else:
                activity_info = "No activity recorded"
            
            self.stdout.write(
                f"  Session {session.session_key[:8]}... - {user_info} - {activity_info}"
            )

    def expire_all_sessions(self):
        """Expire all active sessions"""
        sessions = Session.objects.filter(expire_date__gt=timezone.now())
        count = sessions.count()
        
        # Set expire date to past
        sessions.update(expire_date=timezone.now() - timedelta(seconds=1))
        
        self.stdout.write(
            self.style.SUCCESS(f'Expired {count} active sessions')
        )

    def expire_user_sessions(self, email):
        """Expire sessions for a specific user"""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} not found')
            )
            return

        # Find sessions for this user
        sessions = Session.objects.filter(expire_date__gt=timezone.now())
        user_sessions = []
        
        for session in sessions:
            session_data = session.get_decoded()
            if session_data.get('_auth_user_id') == str(user.id):
                user_sessions.append(session)
        
        if user_sessions:
            # Expire the sessions
            for session in user_sessions:
                session.expire_date = timezone.now() - timedelta(seconds=1)
                session.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Expired {len(user_sessions)} sessions for user {email}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'No active sessions found for user {email}')
            )