# Generated migration for student performance models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('class', '0025_facilitatortask'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=20, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PerformanceCutoff',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('passing_score', models.IntegerField(default=40, help_text='Minimum score to pass (0-100)')),
                ('excellent_score', models.IntegerField(default=80, help_text='Score for excellent performance (0-100)')),
                ('good_score', models.IntegerField(default=60, help_text='Score for good performance (0-100)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('class_section', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='performance_cutoff', to='class.classsection')),
            ],
            options={
                'verbose_name_plural': 'Performance Cutoffs',
            },
        ),
        migrations.CreateModel(
            name='StudentPerformance',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('score', models.IntegerField(help_text='Score out of 100')),
                ('grade', models.CharField(choices=[('A', 'Excellent (80-100)'), ('B', 'Good (60-79)'), ('C', 'Average (40-59)'), ('F', 'Failed (0-39)')], default='C', max_length=1)),
                ('remarks', models.TextField(blank=True, help_text='Teacher remarks')),
                ('recorded_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('class_section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_performances', to='class.classsection')),
                ('recorded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_performances', to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='performance_records', to='class.student')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_performances', to='class.subject')),
            ],
            options={
                'ordering': ['-recorded_date'],
                'unique_together': {('student', 'class_section', 'subject')},
            },
        ),
        migrations.CreateModel(
            name='StudentPerformanceSummary',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('average_score', models.FloatField(default=0, help_text='Average score across all subjects')),
                ('total_subjects', models.IntegerField(default=0)),
                ('passed_subjects', models.IntegerField(default=0)),
                ('failed_subjects', models.IntegerField(default=0)),
                ('rank', models.IntegerField(blank=True, help_text='Rank in class', null=True)),
                ('is_passed', models.BooleanField(default=False, help_text='Overall pass/fail status')),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('class_section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='performance_summaries', to='class.classsection')),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='performance_summary', to='class.student')),
            ],
            options={
                'ordering': ['rank'],
                'unique_together': {('student', 'class_section')},
            },
        ),
        migrations.AddIndex(
            model_name='studentperformance',
            index=models.Index(fields=['student', 'class_section'], name='class_studen_student_idx'),
        ),
        migrations.AddIndex(
            model_name='studentperformance',
            index=models.Index(fields=['class_section', 'subject'], name='class_studen_class_s_idx'),
        ),
    ]
