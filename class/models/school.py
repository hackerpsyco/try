from django.db import models
import uuid

class School(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    udise = models.CharField(max_length=50, unique=True)
    block = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    status = models.SmallIntegerField(default=1)
    enrolled_students = models.IntegerField(default=0)
    avg_attendance_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    validation_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    profile_image = models.ImageField(upload_to="schools/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
