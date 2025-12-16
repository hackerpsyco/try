from django.db import models
import uuid
from .school import School # Import the School model

class ClassSection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='class_sections')
    class_level = models.CharField(max_length=8)
    section = models.CharField(max_length=8, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('school', 'class_level', 'section')
        verbose_name = "Class Section"
        verbose_name_plural = "Class Sections"

    def __str__(self):
        return f"{self.school.name} - Class {self.class_level}{self.section or ''}"
