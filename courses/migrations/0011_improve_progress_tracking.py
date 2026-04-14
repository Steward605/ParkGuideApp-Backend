# courses/migrations/0011_improve_progress_tracking.py
# Generated migration for improved progress tracking

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0010_alter_course_code'),
    ]

    operations = [
        # Add new fields to ChapterProgress
        migrations.AddField(
            model_name='chapterprogress',
            name='practice_attempts',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='chapterprogress',
            name='practice_passed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='chapterprogress',
            name='quiz_attempts',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='chapterprogress',
            name='started_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='chapterprogress',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Add new fields to CourseEnrollment
        migrations.AddField(
            model_name='courseenrollment',
            name='completed_chapters',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='total_chapters',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='total_time_spent',
            field=models.PositiveIntegerField(default=0, help_text='Total time in seconds'),
        ),
        # Add discontinued status option
        migrations.AlterField(
            model_name='courseenrollment',
            name='status',
            field=models.CharField(
                choices=[
                    ('enrolled', 'Enrolled'),
                    ('in_progress', 'In Progress'),
                    ('completed', 'Completed'),
                    ('failed', 'Failed'),
                    ('discontinued', 'Discontinued'),
                ],
                default='enrolled',
                max_length=20
            ),
        ),
        # Add indexes to improve query performance
        migrations.AddIndex(
            model_name='chapterprogress',
            index=models.Index(
                fields=['user', 'is_complete'],
                name='courses_cha_user_id_complete_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='chapterprogress',
            index=models.Index(
                fields=['user', 'chapter'],
                name='courses_cha_user_id_chapter_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='chapterprogress',
            index=models.Index(
                fields=['completed_at'],
                name='courses_cha_complet_at_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='courseenrollment',
            index=models.Index(
                fields=['user', 'status'],
                name='courses_cou_user_id_status_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='courseenrollment',
            index=models.Index(
                fields=['user', 'course'],
                name='courses_cou_user_id_course_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='courseenrollment',
            index=models.Index(
                fields=['status'],
                name='courses_cou_status_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='courseenrollment',
            index=models.Index(
                fields=['completed_date'],
                name='courses_cou_complet_date_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='lessonprogress',
            index=models.Index(
                fields=['user', 'completed'],
                name='courses_les_user_id_completed_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='lessonprogress',
            index=models.Index(
                fields=['user', 'lesson'],
                name='courses_les_user_id_lesson_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='lessonprogress',
            index=models.Index(
                fields=['completed_at'],
                name='courses_les_complet_at_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='practiceattempt',
            index=models.Index(
                fields=['user', 'exercise'],
                name='courses_pra_user_id_exercise_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='practiceattempt',
            index=models.Index(
                fields=['user', 'passed'],
                name='courses_pra_user_id_passed_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='practiceattempt',
            index=models.Index(
                fields=['completed_at'],
                name='courses_pra_complet_at_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='quizattempt',
            index=models.Index(
                fields=['user', 'quiz'],
                name='courses_qui_user_id_quiz_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='quizattempt',
            index=models.Index(
                fields=['user', 'passed'],
                name='courses_qui_user_id_passed_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='quizattempt',
            index=models.Index(
                fields=['completed_at'],
                name='courses_qui_complet_at_idx',
            ),
        ),
        # Add unique constraints for attempt tracking
        migrations.AlterUniqueTogether(
            name='practiceattempt',
            unique_together={('user', 'exercise', 'attempt_number')},
        ),
        migrations.AlterUniqueTogether(
            name='quizattempt',
            unique_together={('user', 'quiz', 'attempt_number')},
        ),
    ]
