from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

# ============================================================================
# COURSE DEFINITION MODELS (Content)
# ============================================================================

class Course(models.Model):
    """Container for all course information"""
    code = models.CharField(max_length=50, help_text="Course code (e.g., 'park-guide-101')")
    title = models.JSONField(help_text="Multilingual title {en, ms, zh}")
    description = models.JSONField(blank=True, null=True, help_text="Multilingual description")
    thumbnail = models.URLField(blank=True, null=True, help_text="Course thumbnail image URL")
    
    # Prerequisites & availability
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True, help_text="Courses that must be completed first")
    is_published = models.BooleanField(default=True, help_text="Is this course available for enrollment?")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.title.get('en', 'Untitled')}"


class Chapter(models.Model):
    """Chapters organize lessons within a course"""
    course = models.ForeignKey(Course, related_name='chapters', on_delete=models.CASCADE)
    title = models.JSONField(help_text="Multilingual chapter title")
    description = models.JSONField(blank=True, null=True, help_text="Optional multilingual description")
    order = models.PositiveIntegerField(default=0, help_text="Display order within course")
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['course', 'order']
        unique_together = ('course', 'order')

    def __str__(self):
        return f"Ch {self.order}: {self.title.get('en', 'Untitled')} - {self.course.code}"


class Lesson(models.Model):
    """Individual lessons within a chapter (the actual learning content)"""
    chapter = models.ForeignKey(Chapter, related_name='lessons', on_delete=models.CASCADE)
    title = models.JSONField(help_text="Multilingual lesson title")
    
    # Rich content support
    content_text = models.JSONField(blank=True, null=True, help_text="Multilingual markdown/HTML content")
    content_images = models.JSONField(default=list, help_text="List of image URLs")
    content_videos = models.JSONField(default=list, help_text="List of {url, title, description}")
    
    order = models.PositiveIntegerField(default=0, help_text="Display order within chapter")
    estimated_time = models.PositiveIntegerField(default=10, help_text="Estimated reading time in minutes")
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['chapter', 'order']
        unique_together = ('chapter', 'order')

    def __str__(self):
        return f"Lesson {self.order}: {self.title.get('en', 'Untitled')}"


class PracticeExercise(models.Model):
    """Practice problems/scenarios within a chapter - comes AFTER lesson"""
    EXERCISE_TYPE_CHOICES = [
        ('multiple_choice', 'Multiple Choice'),
        ('scenario', 'Interactive Scenario'),
        ('mixed', 'Mixed Questions'),
    ]
    
    chapter = models.ForeignKey(Chapter, related_name='practice_exercises', on_delete=models.CASCADE)
    title = models.JSONField(help_text="Multilingual practice title")
    description = models.JSONField(blank=True, null=True)
    
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPE_CHOICES, default='multiple_choice')
    questions = models.JSONField(help_text="Array of {type, question, options, correct_answer, explanation}")
    
    passing_score = models.IntegerField(default=70, validators=[MinValueValidator(0), MaxValueValidator(100)])
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['chapter', 'order']
        unique_together = ('chapter', 'order')

    def __str__(self):
        return f"Practice {self.order}: {self.title.get('en', 'Untitled')}"


class Quiz(models.Model):
    """Final assessment quiz for a chapter - comes AFTER practice"""
    chapter = models.ForeignKey(Chapter, related_name='quizzes', on_delete=models.CASCADE)
    title = models.JSONField(help_text="Multilingual quiz title")
    description = models.JSONField(blank=True, null=True)
    
    questions = models.JSONField(help_text="Array of {type, question, options, correct_answer, explanation}")
    passing_score = models.IntegerField(default=70, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    time_limit = models.IntegerField(blank=True, null=True, help_text="Time limit in minutes, none if null")
    show_answers = models.BooleanField(default=True, help_text="Show correct answers after submission?")
    
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['chapter', 'order']
        unique_together = ('chapter', 'order')

    def __str__(self):
        return f"Quiz: {self.title.get('en', 'Untitled')} - {self.chapter.course.code}"


# ============================================================================
# ENROLLMENT & PROGRESS MODELS
# ============================================================================

class CourseEnrollment(models.Model):
    """Track user enrollment and course progression"""
    STATUS_CHOICES = [
        ('enrolled', 'Enrolled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('discontinued', 'Discontinued'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    started_date = models.DateTimeField(blank=True, null=True)
    completed_date = models.DateTimeField(blank=True, null=True)
    
    # Progress tracking
    completed_chapters = models.PositiveIntegerField(default=0)
    total_chapters = models.PositiveIntegerField(default=0)
    progress_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    final_score = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Time tracking
    total_time_spent = models.PositiveIntegerField(default=0, help_text="Total time in seconds")
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'course')
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'course']),
            models.Index(fields=['status']),
            models.Index(fields=['completed_date']),
        ]
        ordering = ['-updated_at']

    def calculate_progress_percentage(self):
        """Calculate course progress based on chapters"""
        if self.total_chapters == 0:
            return 0
        return (self.completed_chapters / self.total_chapters) * 100

    def __str__(self):
        return f"{self.user.email} - {self.course.code} ({self.status})"


class ChapterProgress(models.Model):
    """Track completion of each chapter with comprehensive metrics"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chapter_progress')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='user_progress')
    
    # Lesson tracking
    completed_lessons = models.PositiveIntegerField(default=0)
    total_lessons = models.PositiveIntegerField(default=0)
    
    # Practice tracking
    practice_completed = models.BooleanField(default=False)
    practice_score = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    practice_attempts = models.PositiveIntegerField(default=0)
    practice_passed = models.BooleanField(default=False)
    
    # Quiz tracking
    quiz_completed = models.BooleanField(default=False)
    quiz_score = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    quiz_attempts = models.PositiveIntegerField(default=0)
    quiz_passed = models.BooleanField(default=False)
    
    # Overall progress
    progress_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_complete = models.BooleanField(default=False)
    
    # Timestamps
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'chapter')
        indexes = [
            models.Index(fields=['user', 'is_complete']),
            models.Index(fields=['user', 'chapter']),
            models.Index(fields=['completed_at']),
        ]
        ordering = ['-updated_at']

    def calculate_progress_percentage(self):
        """Calculate overall chapter progress as weighted average"""
        weights = {
            'lessons': 0.4,      # 40% - lesson completion
            'practice': 0.3,     # 30% - practice score
            'quiz': 0.3,         # 30% - quiz score
        }
        
        # Lesson progress (0-100%)
        lesson_progress = (self.completed_lessons / self.total_lessons * 100) if self.total_lessons > 0 else 0
        
        # Practice progress
        practice_progress = self.practice_score if self.practice_completed else 0
        
        # Quiz progress
        quiz_progress = self.quiz_score if self.quiz_completed else 0
        
        # Weighted total
        total = (lesson_progress * weights['lessons'] +
                practice_progress * weights['practice'] +
                quiz_progress * weights['quiz'])
        
        return min(100, max(0, total))

    def __str__(self):
        return f"{self.user.username} - {self.chapter} ({self.progress_percentage:.0f}%)"


class LessonProgress(models.Model):
    """Track lesson view completion"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='user_progress')
    
    completed = models.BooleanField(default=False)
    time_spent = models.PositiveIntegerField(default=0, help_text="Time spent in seconds")
    last_viewed = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'lesson')
        indexes = [
            models.Index(fields=['user', 'completed']),
            models.Index(fields=['user', 'lesson']),
            models.Index(fields=['completed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.lesson}"


class PracticeAttempt(models.Model):
    """Track practice exercise attempts"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='practice_attempts')
    exercise = models.ForeignKey(PracticeExercise, on_delete=models.CASCADE, related_name='attempts')
    
    attempt_number = models.PositiveIntegerField(default=1)
    answers = models.JSONField(help_text="User's answers {question_idx: selected_answer}")
    score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    passed = models.BooleanField(default=False)
    
    attempted_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user', 'exercise']),
            models.Index(fields=['user', 'passed']),
            models.Index(fields=['completed_at']),
        ]
        unique_together = ('user', 'exercise', 'attempt_number')

    def __str__(self):
        return f"{self.user.email} - {self.exercise} (Attempt {self.attempt_number})"


class QuizAttempt(models.Model):
    """Track quiz attempts and scoring"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    
    attempt_number = models.PositiveIntegerField(default=1)
    answers = models.JSONField(help_text="User's answers {question_idx: selected_answer}")
    score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    passed = models.BooleanField(default=False)
    
    time_spent = models.PositiveIntegerField(default=0, help_text="Time spent in seconds")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user', 'quiz']),
            models.Index(fields=['user', 'passed']),
            models.Index(fields=['completed_at']),
        ]
        unique_together = ('user', 'quiz', 'attempt_number')

    def __str__(self):
        return f"{self.user.email} - {self.quiz} (Score: {self.score}%)"


# ============================================================================
# LEGACY MODELS (for backwards compatibility during transition)
# ============================================================================

class Module(models.Model):
    """Legacy module - kept for backwards compatibility"""
    code = models.CharField(max_length=10, blank=True, null=True)
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.JSONField()
    content = models.JSONField(blank=True, null=True)
    quiz = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.code or self.id} - {self.title.get('en', 'Untitled')}"


class ModuleProgress(models.Model):
    """Legacy progress model"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'module')

    def __str__(self):
        return f"{self.user} - {self.module}"


class CourseProgress(models.Model):
    """Legacy course progress model"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    completed_modules = models.PositiveIntegerField(default=0)
    total_modules = models.PositiveIntegerField(default=0)
    progress = models.FloatField(default=0)
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user} - {self.course} ({self.progress:.0%})"