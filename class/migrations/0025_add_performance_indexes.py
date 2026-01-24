# Generated migration for performance optimization
# Adds critical indexes to improve query performance

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('class', '0037_cluster_school_cluster'),
    ]

    operations = [
        # PlannedSession indexes
        migrations.AddIndex(
            model_name='plannedsession',
            index=models.Index(fields=['class_section', 'day_number'], name='ps_class_day_idx'),
        ),
        migrations.AddIndex(
            model_name='plannedsession',
            index=models.Index(fields=['class_section', 'is_active'], name='ps_class_active_idx'),
        ),
        
        # ActualSession indexes
        migrations.AddIndex(
            model_name='actualsession',
            index=models.Index(fields=['date'], name='as_date_idx'),
        ),
        migrations.AddIndex(
            model_name='actualsession',
            index=models.Index(fields=['facilitator', 'date'], name='as_fac_date_idx'),
        ),
        migrations.AddIndex(
            model_name='actualsession',
            index=models.Index(fields=['status', 'date'], name='as_status_date_idx'),
        ),
        migrations.AddIndex(
            model_name='actualsession',
            index=models.Index(fields=['planned_session', 'date'], name='as_ps_date_idx'),
        ),
        
        # Attendance indexes
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(fields=['actual_session'], name='att_as_idx'),
        ),
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(fields=['enrollment'], name='att_enroll_idx'),
        ),
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(fields=['status', 'marked_at'], name='att_status_time_idx'),
        ),
        
        # ClassSection indexes
        migrations.AddIndex(
            model_name='classsection',
            index=models.Index(fields=['school', 'is_active'], name='cs_school_active_idx'),
        ),
        
        # Student indexes
        migrations.AddIndex(
            model_name='student',
            index=models.Index(fields=['enrollment_number'], name='st_enroll_num_idx'),
        ),
        
        # Enrollment indexes
        migrations.AddIndex(
            model_name='enrollment',
            index=models.Index(fields=['school', 'is_active'], name='enroll_school_active_idx'),
        ),
    ]
