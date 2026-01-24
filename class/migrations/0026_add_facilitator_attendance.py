# Generated migration for facilitator attendance

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('class', '0025_add_performance_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='actualsession',
            name='facilitator_attendance',
            field=models.CharField(
                blank=True,
                choices=[('present', 'Present'), ('absent', 'Absent'), ('leave', 'Leave'), ('', 'Not Marked')],
                default='',
                help_text='Facilitator attendance status',
                max_length=10
            ),
        ),
    ]
