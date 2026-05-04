"""
AR Training Models
Manages AR scenarios, progress tracking, quiz results, and achievements
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class ARScenario(models.Model):
    """Base AR scenario template"""
    TYPE_CHOICES = [
        ('forest', 'Forest Biodiversity'),
        ('eco', 'Eco-tourism'),
        ('wildlife', 'Wildlife Safety'),
    ]
    
    code = models.CharField(max_length=100, unique=True, help_text="Unique scenario code (e.g., 'ar-biodiversity-101')")
    title = models.JSONField(help_text="Multilingual title {en, ms, zh}")
    description = models.JSONField(blank=True, null=True, help_text="Multilingual description")
    
    scenario_type = models.CharField(max_length=20, choices=TYPE_CHOICES, help_text="Type of AR scenario")
    difficulty = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        default='intermediate'
    )
    
    duration_minutes = models.PositiveIntegerField(default=20, help_text="Estimated training duration")
    thumbnail = models.URLField(blank=True, null=True, help_text="Scenario thumbnail")
    
    is_published = models.BooleanField(default=True, help_text="Is this scenario available?")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
        indexes = [
            models.Index(fields=['scenario_type', 'is_published']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.title.get('en', 'Untitled')}"


class AREnvironment(models.Model):
    """Environment images for AR scenarios"""
    scenario = models.ForeignKey(ARScenario, related_name='environments', on_delete=models.CASCADE)
    
    name = models.CharField(max_length=100, help_text="Environment name (e.g., 'Tropical Rainforest')")
    description = models.JSONField(blank=True, null=True, help_text="Multilingual environment description")
    
    panorama_url = models.URLField(help_text="High-resolution panoramic image URL")
    thumbnail_url = models.URLField(blank=True, null=True, help_text="Thumbnail image URL")
    
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['scenario', 'order']
        unique_together = ('scenario', 'name')
    
    def __str__(self):
        return f"{self.name} - {self.scenario.code}"


class ARHotspot(models.Model):
    """Interactive hotspots within AR scenarios"""
    scenario = models.ForeignKey(ARScenario, related_name='hotspots', on_delete=models.CASCADE)
    
    hotspot_id = models.CharField(max_length=100, help_text="Unique identifier for hotspot")
    title = models.JSONField(help_text="Multilingual hotspot title")
    
    # Position in panoramic view (0-100)
    position_x = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    position_y = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Content
    content = models.JSONField(help_text="""
        {
            "species": "Species name",
            "scientific": "Scientific name",
            "height": "Physical dimensions",
            "characteristics": {"en": "...", "ms": "...", "zh": "..."},
            "ecology": {"en": "...", "ms": "...", "zh": "..."},
            "wildlife": ["associated", "species"],
            "safeDistance": "100+ meters",
            "actionPlan": {"en": "...", "ms": "...", "zh": "..."}
        }
    """)
    
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['scenario', 'order']
        unique_together = ('scenario', 'hotspot_id')
    
    def __str__(self):
        return f"{self.title.get('en', 'Untitled')} - {self.scenario.code}"


class ARQuizQuestion(models.Model):
    """Quiz questions for AR scenarios"""
    scenario = models.ForeignKey(ARScenario, related_name='quiz_questions', on_delete=models.CASCADE)
    
    question_id = models.CharField(max_length=100)
    question_text = models.JSONField(help_text="Multilingual question {en, ms, zh}")
    
    # Multiple choice options
    options = models.JSONField(help_text="Multilingual options {en: [...], ms: [...], zh: [...]}")
    correct_option = models.PositiveIntegerField(help_text="Index of correct option (0-3)")
    
    explanation = models.JSONField(help_text="Multilingual explanation {en, ms, zh}")
    
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['scenario', 'order']
        unique_together = ('scenario', 'question_id')
    
    def __str__(self):
        return f"Q{self.order}: {self.scenario.code}"


class ARTrainingProgress(models.Model):
    """Track user progress through AR scenarios"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ar_training_progress')
    scenario = models.ForeignKey(ARScenario, on_delete=models.CASCADE, related_name='user_progress')
    
    # Visited hotspots
    visited_hotspots = models.JSONField(default=list, help_text="List of visited hotspot IDs")
    
    # Time tracking
    time_spent_seconds = models.PositiveIntegerField(default=0, help_text="Total time spent on this scenario")
    
    # Progress metrics
    completion_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_completed = models.BooleanField(default=False)
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ('user', 'scenario')
        indexes = [
            models.Index(fields=['user', 'scenario']),
            models.Index(fields=['user', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.scenario.code} ({self.completion_percentage}%)"


class ARQuizResult(models.Model):
    """Store quiz attempt results"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ar_quiz_results')
    scenario = models.ForeignKey(ARScenario, on_delete=models.CASCADE, related_name='quiz_results')
    
    # Answers
    answers = models.JSONField(help_text="User's answers {question_id: option_index}")
    
    # Scoring
    score = models.PositiveIntegerField(help_text="Number of correct answers")
    total_questions = models.PositiveIntegerField(help_text="Total number of questions")
    percentage = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage score"
    )
    passed = models.BooleanField(default=False)
    
    # Time tracking
    time_spent_seconds = models.PositiveIntegerField(help_text="Time taken for quiz")
    
    # Timestamp
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user', 'scenario', '-completed_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.scenario.code} - {self.percentage}%"


class ARBadge(models.Model):
    """Achievement badges for AR training"""
    badge_id = models.CharField(max_length=100, unique=True, help_text="Unique badge identifier")
    name = models.CharField(max_length=200, help_text="Badge name")
    description = models.JSONField(help_text="Multilingual description {en, ms, zh}")
    
    icon = models.CharField(max_length=100, help_text="Icon name (Material Design)")
    requirement = models.CharField(max_length=500, help_text="Human-readable requirement")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['badge_id']
    
    def __str__(self):
        return self.badge_id


class ARUserAchievement(models.Model):
    """Track user achievements and badges"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ar_achievements')
    badge = models.ForeignKey(ARBadge, on_delete=models.CASCADE, related_name='users')
    
    unlocked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-unlocked_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.badge.badge_id}"


class ARTrainingStatistics(models.Model):
    """Aggregate training statistics for users"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ar_statistics')
    
    # Summary metrics
    total_scenarios_completed = models.PositiveIntegerField(default=0)
    total_hotspots_visited = models.PositiveIntegerField(default=0)
    average_quiz_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    total_training_hours = models.FloatField(default=0)
    
    # Streaks
    current_streak_days = models.PositiveIntegerField(default=0)
    longest_streak_days = models.PositiveIntegerField(default=0)
    last_training_date = models.DateField(blank=True, null=True)
    
    # Updated
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "AR Training Statistics"
    
    def __str__(self):
        return f"Stats: {self.user.email}"
