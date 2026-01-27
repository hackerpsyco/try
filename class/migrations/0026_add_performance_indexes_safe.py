# Generated migration - SAFE: Only adds indexes, no data changes
# This migration adds critical database indexes to fix N+1 query problems
# NO DATA WILL BE LOST OR MODIFIED

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('class', '0025_add_performance_indexes'),
    ]

    operations = [
        # ============================================================
        # ENROLLMENT INDEXES - Fix N+1 queries on student lists
        # ============================================================
        migrations.AddIndex(
            model_name='enrollment',
            index=models.Index(
                fields=['school', 'is_active', 'start_date'],
                name='enroll_sch_active_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='enrollment',
            index=models.Index(
                fields=['class_section', 'is_active'],
                name='enroll_cls_active_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='enrollment',
            index=models.Index(
                fields=['student', 'is_active'],
                name='enroll_stud_active_idx'
            ),
        ),

        # ============================================================
        # ATTENDANCE INDEXES - Fix attendance report queries
        # ============================================================
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(
                fields=['student_id', 'marked_at'],
                name='attend_stud_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(
                fields=['class_section_id', 'marked_at'],
                name='attend_cls_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(
                fields=['school_id', 'marked_at'],
                name='attend_sch_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(
                fields=['status', 'marked_at'],
                name='attend_status_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(
                fields=['actual_session', 'enrollment'],
                name='attend_sess_enroll_idx'
            ),
        ),

        # ============================================================
        # ACTUAL SESSION INDEXES - Fix session lookups
        # ============================================================
        migrations.AddIndex(
            model_name='actualsession',
            index=models.Index(
                fields=['planned_session', 'status'],
                name='asess_sess_stat_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='actualsession',
            index=models.Index(
                fields=['date', 'status'],
                name='asess_date_stat_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='actualsession',
            index=models.Index(
                fields=['facilitator', 'date'],
                name='asess_facil_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='actualsession',
            index=models.Index(
                fields=['status', 'date'],
                name='asess_stat_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='actualsession',
            index=models.Index(
                fields=['attendance_marked', 'date'],
                name='asess_attend_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='actualsession',
            index=models.Index(
                fields=['conducted_at'],
                name='asess_conducted_idx'
            ),
        ),

        # ============================================================
        # PLANNED SESSION INDEXES - Fix day lookups
        # ============================================================
        migrations.AddIndex(
            model_name='plannedsession',
            index=models.Index(
                fields=['class_section', 'day_number'],
                name='psess_cls_day_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='plannedsession',
            index=models.Index(
                fields=['class_section', 'is_active'],
                name='psess_cls_active_idx'
            ),
        ),

        # ============================================================
        # SESSION FEEDBACK INDEXES - Fix feedback queries
        # ============================================================
        migrations.AddIndex(
            model_name='sessionfeedback',
            index=models.Index(
                fields=['facilitator', 'is_complete'],
                name='sfeed_facil_complete_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='sessionfeedback',
            index=models.Index(
                fields=['feedback_date'],
                name='sfeed_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='sessionfeedback',
            index=models.Index(
                fields=['actual_session', 'facilitator'],
                name='sfeed_sess_facil_idx'
            ),
        ),

        # ============================================================
        # FACILITATOR SCHOOL INDEXES - Fix facilitator lookups
        # ============================================================
        # Note: These will be added if FacilitatorSchool model exists
        # migrations.AddIndex(
        #     model_name='facilitatorschool',
        #     index=models.Index(
        #         fields=['facilitator', 'is_active'],
        #         name='fsch_facil_active_idx'
        #     ),
        # ),
        # migrations.AddIndex(
        #     model_name='facilitatorschool',
        #     index=models.Index(
        #         fields=['school', 'is_active'],
        #         name='fsch_sch_active_idx'
        #     ),
        # ),

        # ============================================================
        # SESSION STEP INDEXES - Fix activity lookups
        # ============================================================
        migrations.AddIndex(
            model_name='sessionstep',
            index=models.Index(
                fields=['planned_session', 'order'],
                name='sstep_sess_order_idx'
            ),
        ),

        # ============================================================
        # LESSON PLAN UPLOAD INDEXES - Fix upload queries
        # ============================================================
        migrations.AddIndex(
            model_name='lessonplanupload',
            index=models.Index(
                fields=['facilitator', 'upload_date'],
                name='lplan_facil_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='lessonplanupload',
            index=models.Index(
                fields=['planned_session', 'facilitator'],
                name='lplan_sess_facil_idx'
            ),
        ),

        # ============================================================
        # SESSION REWARD INDEXES - Fix reward queries
        # ============================================================
        migrations.AddIndex(
            model_name='sessionreward',
            index=models.Index(
                fields=['facilitator', 'reward_date'],
                name='sreward_facil_date_idx'
            ),
        ),

        # ============================================================
        # SESSION PREPARATION CHECKLIST INDEXES
        # ============================================================
        migrations.AddIndex(
            model_name='sessionpreparationchecklist',
            index=models.Index(
                fields=['facilitator', 'preparation_start_time'],
                name='sprep_facil_start_idx'
            ),
        ),

        # ============================================================
        # STUDENT FEEDBACK INDEXES
        # ============================================================
        migrations.AddIndex(
            model_name='studentfeedback',
            index=models.Index(
                fields=['actual_session', 'submitted_at'],
                name='stfeed_sess_date_idx'
            ),
        ),

        # ============================================================
        # TEACHER FEEDBACK INDEXES
        # ============================================================
        migrations.AddIndex(
            model_name='teacherfeedback',
            index=models.Index(
                fields=['actual_session', 'submitted_at'],
                name='tfeed_sess_date_idx'
            ),
        ),

        # ============================================================
        # FACILITATOR TASK INDEXES - Fix task queries
        # ============================================================
        migrations.AddIndex(
            model_name='facilitatortask',
            index=models.Index(
                fields=['facilitator', 'created_at'],
                name='ftask_facil_date_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='facilitatortask',
            index=models.Index(
                fields=['status', 'created_at'],
                name='ftask_status_date_idx'
            ),
        ),
    ]
