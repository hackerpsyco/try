from django.core.management.base import BaseCommand
from class.models import User, Role

class Command(BaseCommand):
    help = 'Create default admin user'

    def handle(self, *args, **kwargs):
        role, _ = Role.objects.get_or_create(id=0, defaults={"name": "Admin"})

        if not User.objects.filter(email="admin@example.com").exists():
            u = User.objects.create_superuser(
                email="piyushmodi812@gmail.com",
                password="wes@123"
            )
            u.role = role
            u.save()
            self.stdout.write(self.style.SUCCESS('Admin user created'))
        else:
            self.stdout.write(self.style.WARNING('Admin already exists'))