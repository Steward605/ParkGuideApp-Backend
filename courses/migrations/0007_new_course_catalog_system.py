# Generated migration for new course catalog system

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0006_course_code'),
    ]

    operations = [
        # Add nullable fields to Course
        migrations.AddField(
            model_name='course',
            name='description',
            field=models.JSONField(blank=True, null=True, help_text="Multilingual description"),
        ),
        migrations.AddField(
            model_name='course',
            name='thumbnail',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='is_published',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='course',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, blank=True),
        ),
        
        # Create Chapter model
        migrations.CreateModel(
            name='Chapter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.JSONField(help_text='Multilingual chapter title')),
                ('description', models.JSONField(blank=True, null=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, blank=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chapters', to='courses.course')),
            ],
            options={
                'ordering': ['course', 'order'],
            },
        ),
        
        # Create Lesson model
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.JSONField()),
                ('content_text', models.JSONField(blank=True, null=True)),
                ('content_images', models.JSONField(default=list)),
                ('content_videos', models.JSONField(default=list)),
                ('order', models.PositiveIntegerField(default=0)),
                ('estimated_time', models.PositiveIntegerField(default=10)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, blank=True)),
                ('chapter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='courses.chapter')),
            ],
            options={
                'ordering': ['chapter', 'order'],
            },
        ),
        
        # Create PracticeExercise model
        migrations.CreateModel(
            name='PracticeExercise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.JSONField()),
                ('description', models.JSONField(blank=True, null=True)),
                ('exercise_type', models.CharField(choices=[('multiple_choice', 'Multiple Choice'), ('scenario', 'Interactive Scenario'), ('mixed', 'Mixed Questions')], default='multiple_choice', max_length=20)),
                ('questions', models.JSONField()),
                ('passing_score', models.IntegerField(default=70, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, blank=True)),
                ('chapter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='practice_exercises', to='courses.chapter')),
            ],
            options={
                'ordering': ['chapter', 'order'],
            },
        ),
        
        # Create Quiz model
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.JSONField()),
                ('description', models.JSONField(blank=True, null=True)),
                ('questions', models.JSONField()),
                ('passing_score', models.IntegerField(default=70, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('time_limit', models.IntegerField(blank=True, null=True)),
                ('show_answers', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, blank=True)),
                ('chapter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quizzes', to='courses.chapter')),
            ],
            options={
                'ordering': ['chapter', 'order'],
            },
        ),
        
        # Create CourseEnrollment model
        migrations.CreateModel(
            name='CourseEnrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('enrolled', 'Enrolled'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('failed', 'Failed')], default='enrolled', max_length=20)),
                ('enrollment_date', models.DateTimeField(auto_now_add=True)),
                ('started_date', models.DateTimeField(blank=True, null=True)),
                ('completed_date', models.DateTimeField(blank=True, null=True)),
                ('progress_percentage', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('final_score', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='courses.course')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_enrollments', to='accounts.customuser')),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        
        # Create ChapterProgress model
        migrations.CreateModel(
            name='ChapterProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed_lessons', models.PositiveIntegerField(default=0)),
                ('total_lessons', models.PositiveIntegerField(default=0)),
                ('practice_completed', models.BooleanField(default=False)),
                ('practice_score', models.FloatField(blank=True, null=True)),
                ('quiz_completed', models.BooleanField(default=False)),
                ('quiz_score', models.FloatField(blank=True, null=True)),
                ('quiz_passed', models.BooleanField(default=False)),
                ('progress_percentage', models.FloatField(default=0)),
                ('is_complete', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('chapter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.chapter')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.customuser')),
            ],
        ),
        
        # Create LessonProgress model
        migrations.CreateModel(
            name='LessonProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed', models.BooleanField(default=False)),
                ('time_spent', models.PositiveIntegerField(default=0)),
                ('last_viewed', models.DateTimeField(auto_now=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.lesson')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.customuser')),
            ],
        ),
        
        # Create PracticeAttempt model
        migrations.CreateModel(
            name='PracticeAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attempt_number', models.PositiveIntegerField(default=1)),
                ('answers', models.JSONField()),
                ('score', models.FloatField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('passed', models.BooleanField(default=False)),
                ('attempted_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(auto_now=True)),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='courses.practiceexercise')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.customuser')),
            ],
            options={
                'ordering': ['-completed_at'],
            },
        ),
        
        # Create QuizAttempt model
        migrations.CreateModel(
            name='QuizAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attempt_number', models.PositiveIntegerField(default=1)),
                ('answers', models.JSONField()),
                ('score', models.FloatField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('passed', models.BooleanField(default=False)),
                ('time_spent', models.PositiveIntegerField(default=0)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(auto_now=True)),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='courses.quiz')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.customuser')),
            ],
            options={
                'ordering': ['-completed_at'],
            },
        ),
        
        # Add unique constraints
        migrations.AddConstraint(
            model_name='courseenrollment',
            constraint=models.UniqueConstraint(fields=['user', 'course'], name='unique_user_course_enrollment'),
        ),
        migrations.AddConstraint(
            model_name='chapterprogress',
            constraint=models.UniqueConstraint(fields=['user', 'chapter'], name='unique_user_chapter_progress'),
        ),
        migrations.AddConstraint(
            model_name='lessonprogress',
            constraint=models.UniqueConstraint(fields=['user', 'lesson'], name='unique_user_lesson_progress'),
        ),
        
        # Add M2M prerequisite field
        migrations.AddField(
            model_name='course',
            name='prerequisites',
            field=models.ManyToManyField(blank=True, help_text='Courses that must be completed first', related_name='_course_prerequisites_+', to='courses.course'),
        ),
    ]
