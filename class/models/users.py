import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


# ---------------------------
# Custom User Manager
# ---------------------------
class UserManager(BaseUserManager):

    def create_user(self, email, password=None, role_id=2, full_name=""):
        if not email:
            raise ValueError("Email is required")

        user = self.model(
            email=self.normalize_email(email),
            full_name=full_name,
            role_id=role_id,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email=email, password=password, role_id=0)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


# ---------------------------
# Roles Table
# ---------------------------
class Role(models.Model):
    id = models.SmallIntegerField(primary_key=True)  # 0=Admin, 1=Supervisor, 2=Facilitator
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


# ---------------------------
# Custom User Table
# ---------------------------
class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150, blank=True)

    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)        # REQUIRED FOR ADMIN
    # is_superuser is provided by PermissionsMixin

    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # no username required

    objects = UserManager()

    def __str__(self):
        return self.email
