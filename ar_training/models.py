"""
AR Training Models - Redesigned for Immersive Simulation Experience
Manages immersive VR/AR training scenarios with 360° panoramas, interactive hotspots,
and guided tour experiences for park guide training

Architecture:
- ARSimulationScenario: Core training scenario (biodiversity, wildlife, eco-tourism, etc.)
- AR360Panorama: 360° panoramic image representing an immersive environment
- ARInteractiveHotspot: Interactive elements (learning points, AR overlays, triggers)
- ARScenarioSequence: Order of panoramas/interactions within a scenario (guided tour)
- ARSimulationQuiz: Quick assessment within immersive experience
- User Progress & Achievements: Track completion and learning outcomes
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class ARSimulationScenario(models.Model):
    """Immersive AR/VR training simulation scenario"""
    TYPE_CHOICES = [
        ('biodiversity', 'Forest Biodiversity Training'),
        ('wildlife', 'Wildlife Safety & Encounter'),
        ('ecotourism', 'Eco-tourism Management'),
        ('conservation', 'Conservation & Restoration'),
        ('guiding', 'Professional Guide Skills'),
    ]
    
    IMMERSION_CHOICES = [
        ('guided_tour', 'Guided Tour - Linear narrative'),
        ('exploration', 'Free Exploration - Self-paced'),
        ('simulation', 'Interactive Simulation - Decision-making'),
    ]
    
    code = models.CharField(max_length=100, unique=True, help_text="Unique scenario code")
    title = models.JSONField(help_text="Multilingual title {en, ms, zh}")
    description = models.JSONField(help_text="Detailed scenario description")
    learning_objectives = models.JSONField(help_text="What trainee learns: array of objectives in {en, ms, zh}")
    
    scenario_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    difficulty = models.CharField(
        max_length=20,
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        default='intermediate'
    )
    
    # Immersive experience settings
    duration_minutes = models.PositiveIntegerField(default=8, help_text="Quick 5-10 min browse experience")
    thumbnail = models.URLField(blank=True, null=True, help_text="Scenario thumbnail for list view")
    immersion_type = models.CharField(max_length=20, choices=IMMERSION_CHOICES, default='guided_tour')
    
    # Starting point
    initial_panorama_url = models.URLField(help_text="Starting 360° panorama image")
    intro_audio_url = models.URLField(blank=True, null=True, help_text="Optional intro audio narration")
    intro_audio_duration_seconds = models.PositiveIntegerField(default=0)
    
    # Metadata
    park_location = models.CharField(max_length=200, blank=True, help_text="Which park/area")
    weather_best = models.CharField(max_length=100, blank=True, help_text="Best time/weather to visit")
    safety_warning = models.JSONField(blank=True, null=True, help_text="Optional warnings {en, ms, zh}")
    
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order in list")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['scenario_type', 'is_published']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['is_published', 'order']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.title.get('en', 'Untitled')}"


class AR360Panorama(models.Model):
    """360° panoramic image forming the base of immersive environment"""
    scenario = models.ForeignKey(ARSimulationScenario, related_name='panoramas', on_delete=models.CASCADE)
    
    name = models.CharField(max_length=200, help_text="Location/environment name")
    description = models.JSONField(help_text="Context description {en, ms, zh}")
    
    # High-quality 360° panorama
    panorama_url = models.URLField(help_text="360° panoramic image (equirectangular, 1200x600px min)")
    thumbnail_url = models.URLField(blank=True, null=True, help_text="Thumbnail for preview")
    
    # Ambient audio
    ambient_audio_url = models.URLField(blank=True, null=True, help_text="Background nature sounds")
    ambient_audio_duration_seconds = models.PositiveIntegerField(default=0)
    
    # Panorama metadata
    initial_yaw = models.FloatField(default=0, help_text="Initial camera rotation (degrees)")
    initial_pitch = models.FloatField(default=0, help_text="Initial camera pitch (degrees)")
    
    order = models.PositiveIntegerField(default=1, help_text="Tour sequence")
    is_key_view = models.BooleanField(default=False, help_text="Main observation point")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['scenario', 'order']
        indexes = [
            models.Index(fields=['scenario', 'order']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.scenario.code})"


class ARInteractiveHotspot(models.Model):
    """Interactive elements/learning points in panoramic view"""
    INTERACTION_CHOICES = [
        ('info_card', 'Information Card'),
        ('question', 'Quiz Question'),
        ('audio_narration', 'Audio Narration'),
        ('animation_trigger', 'Animation Trigger'),
        ('3d_object', '3D Object Overlay'),
        ('decision_point', 'Decision Point'),
    ]
    
    panorama = models.ForeignKey(AR360Panorama, related_name='hotspots', on_delete=models.CASCADE)
    scenario = models.ForeignKey(ARSimulationScenario, related_name='all_hotspots', on_delete=models.CASCADE)
    
    hotspot_id = models.CharField(max_length=100, help_text="Unique identifier")
    title = models.JSONField(help_text="Multilingual title {en, ms, zh}")
    
    # 3D Position in panoramic view (equirectangular coordinates)
    position_yaw = models.FloatField(help_text="Horizontal angle (0-360 degrees)")
    position_pitch = models.FloatField(help_text="Vertical angle (-90 to 90 degrees)")
    
    # Interaction type
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_CHOICES)
    
    # Content
    content = models.JSONField(help_text="""
        Flexible content based on type:
        {
            "title": "Display title",
            "subtitle": "Optional subtitle",
            "description": {"en": "", "ms": "", "zh": ""},
            "image_url": "Optional image",
            "audio_url": "Optional audio narration",
            "audio_duration_seconds": 0,
            "keywords": ["tag1", "tag2"],
            "details": "Rich HTML content"
        }
    """)
    
    # Metadata
    color_hint = models.CharField(max_length=7, default="#FF6B6B", help_text="Highlight color for marker")
    icon_type = models.CharField(max_length=50, default="info", help_text="Icon in 3D space")
    
    order = models.PositiveIntegerField(default=0, help_text="Discovery sequence")
    required_visit = models.BooleanField(default=False, help_text="Must visit to complete scenario")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['panorama', 'order']
        unique_together = ('scenario', 'hotspot_id')
        indexes = [
            models.Index(fields=['scenario', 'required_visit']),
            models.Index(fields=['panorama', 'order']),
        ]
    
    def __str__(self):
        return f"{self.hotspot_id} ({self.panorama.name})"


class ARScenarioSequence(models.Model):
    """Defines the order/flow of panoramas and interactions (for guided tours)"""
    scenario = models.ForeignKey(ARSimulationScenario, related_name='sequences', on_delete=models.CASCADE)
    
    step_number = models.PositiveIntegerField(help_text="Order in tour")
    panorama = models.ForeignKey(AR360Panorama, on_delete=models.CASCADE)
    
    # Guidance
    narration_text = models.JSONField(help_text="What guide explains {en, ms, zh}")
    narration_audio_url = models.URLField(blank=True, null=True)
    narration_duration_seconds = models.PositiveIntegerField(default=0)
    
    # Time
    recommended_time_seconds = models.PositiveIntegerField(default=30, help_text="How long to spend here")
    
    class Meta:
        unique_together = ('scenario', 'step_number')
        ordering = ['scenario', 'step_number']
    
    def __str__(self):
        return f"{self.scenario.code} - Step {self.step_number}"


class ARSimulationQuiz(models.Model):
    """Quick quiz questions integrated into immersive experience"""
    scenario = models.ForeignKey(ARSimulationScenario, related_name='quizzes', on_delete=models.CASCADE)
    
    question_id = models.CharField(max_length=100)
    question_text = models.JSONField(help_text="Multilingual question {en, ms, zh}")
    question_image_url = models.URLField(blank=True, null=True, help_text="Optional image with question")
    
    # Options
    options = models.JSONField(help_text="Multilingual options array {en: [], ms: [], zh: []}")
    correct_option_index = models.PositiveIntegerField(help_text="Index of correct option (0-3)")
    
    # Feedback
    correct_explanation = models.JSONField(help_text="Multilingual feedback on correct answer {en, ms, zh}")
    incorrect_explanation = models.JSONField(help_text="Multilingual feedback on wrong answer {en, ms, zh}")
    
    # Metadata
    difficulty_level = models.CharField(max_length=20, choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')])
    time_limit_seconds = models.PositiveIntegerField(default=30, help_text="Time to answer")
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('scenario', 'question_id')
        ordering = ['scenario', 'order']
    
    def __str__(self):
        return f"Q{self.order}: {self.scenario.code}"


class ARTrainingProgress(models.Model):
    """Track user progress through AR simulation"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ar_progress')
    scenario = models.ForeignKey(ARSimulationScenario, on_delete=models.CASCADE)
    
    # Visited/Completed
    panoramas_visited = models.JSONField(default=list, help_text="List of panorama IDs visited")
    hotspots_discovered = models.JSONField(default=list, help_text="List of hotspot IDs discovered")
    quizzes_completed = models.JSONField(default=list, help_text="Quiz results")
    
    # Progress
    completion_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_completed = models.BooleanField(default=False)
    
    # Time
    time_spent_seconds = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'scenario')
        indexes = [
            models.Index(fields=['user', 'is_completed']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.scenario.code} ({self.completion_percentage}%)"


class ARQuizAttempt(models.Model):
    """Store individual quiz attempt within simulation"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ar_quiz_attempts')
    quiz = models.ForeignKey(ARSimulationQuiz, on_delete=models.CASCADE)
    
    user_answer_index = models.PositiveIntegerField(help_text="Index of user's selected option")
    is_correct = models.BooleanField()
    time_taken_seconds = models.PositiveIntegerField()
    
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.user.email} - Q{self.quiz.order} - {'✓' if self.is_correct else '✗'}"


class ARBadge(models.Model):
    """Achievement badges for training milestones"""
    badge_id = models.CharField(max_length=100, unique=True)
    name = models.JSONField(help_text="Multilingual badge name {en, ms, zh}")
    description = models.JSONField(help_text="Multilingual description {en, ms, zh}")
    
    icon_url = models.URLField(help_text="Badge icon image URL")
    requirement = models.CharField(max_length=500, help_text="Human-readable requirement")
    
    class Meta:
        ordering = ['badge_id']
    
    def __str__(self):
        return self.badge_id


class ARUserAchievement(models.Model):
    """Track user achievements and unlocked badges"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ar_badges')
    badge = models.ForeignKey(ARBadge, on_delete=models.CASCADE)
    
    unlocked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-unlocked_at']
    
    def __str__(self):
        return f"{self.user.email} → {self.badge.badge_id}"


class ARTrainingStatistics(models.Model):
    """Aggregate statistics for user's AR training"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ar_stats')
    
    # Completion
    total_scenarios_completed = models.PositiveIntegerField(default=0)
    total_scenarios_attempted = models.PositiveIntegerField(default=0)
    
    # Engagement
    total_hotspots_discovered = models.PositiveIntegerField(default=0)
    total_panoramas_visited = models.PositiveIntegerField(default=0)
    total_quiz_attempts = models.PositiveIntegerField(default=0)
    average_quiz_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Time
    total_training_minutes = models.PositiveIntegerField(default=0)
    
    # Streaks & Engagement
    current_streak_days = models.PositiveIntegerField(default=0)
    longest_streak_days = models.PositiveIntegerField(default=0)
    last_trained_date = models.DateField(blank=True, null=True)
    
    # Metadata
    total_badges_earned = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "AR Training Statistics"
    
    def __str__(self):
        return f"AR Stats: {self.user.email}"
