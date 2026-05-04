"""
AR Training Serializers - Immersive Simulation Experience
Serialization for 360° panoramas and interactive hotspots
"""
from rest_framework import serializers
from ar_training.models import (
    ARSimulationScenario, AR360Panorama, ARInteractiveHotspot,
    ARScenarioSequence, ARSimulationQuiz, ARTrainingProgress,
    ARBadge, ARUserAchievement
)


class ARHotspotSerializer(serializers.ModelSerializer):
    """Interactive hotspots in panoramic views"""
    class Meta:
        model = ARInteractiveHotspot
        fields = [
            'id', 'hotspot_id', 'title', 'position_yaw', 'position_pitch',
            'interaction_type', 'content', 'color_hint', 'icon_type',
            'required_visit', 'order'
        ]


class AR360PanoramaSerializer(serializers.ModelSerializer):
    """360° panoramic environments"""
    hotspots = ARHotspotSerializer(many=True, read_only=True)
    
    class Meta:
        model = AR360Panorama
        fields = [
            'id', 'name', 'description', 'panorama_url', 'thumbnail_url',
            'ambient_audio_url', 'initial_yaw', 'initial_pitch',
            'order', 'is_key_view', 'hotspots'
        ]


class ARScenarioSequenceSerializer(serializers.ModelSerializer):
    """Tour sequence steps"""
    panorama = AR360PanoramaSerializer(read_only=True)
    
    class Meta:
        model = ARScenarioSequence
        fields = [
            'step_number', 'panorama', 'narration_text', 'narration_audio_url',
            'narration_duration_seconds', 'recommended_time_seconds'
        ]


class ARSimulationQuizSerializer(serializers.ModelSerializer):
    """Quiz questions in simulations"""
    class Meta:
        model = ARSimulationQuiz
        fields = [
            'id', 'question_id', 'question_text', 'question_image_url',
            'options', 'difficulty_level', 'time_limit_seconds', 'order'
        ]
        # Don't expose correct answer in list view
        read_only_fields = ['id']
    
    def to_representation(self, instance):
        """Hide correct answer in serialization"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Only show correct answer to authenticated users on POST (answer submission)
        if not request or request.method != 'POST':
            # Keep options but don't reveal which is correct
            pass
        
        return data


class ARScenarioListSerializer(serializers.ModelSerializer):
    """Quick view of scenarios for list"""
    panorama_count = serializers.SerializerMethodField()
    hotspot_count = serializers.SerializerMethodField()
    quiz_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ARSimulationScenario
        fields = [
            'id', 'code', 'title', 'description', 'scenario_type',
            'difficulty', 'duration_minutes', 'thumbnail', 'immersion_type',
            'panorama_count', 'hotspot_count', 'quiz_count'
        ]
    
    def get_panorama_count(self, obj):
        return obj.panoramas.count()
    
    def get_hotspot_count(self, obj):
        return obj.all_hotspots.count()
    
    def get_quiz_count(self, obj):
        return obj.quizzes.count()


class ARScenarioDetailSerializer(serializers.ModelSerializer):
    """Complete scenario details with all content"""
    panoramas = AR360PanoramaSerializer(many=True, read_only=True)
    sequences = ARScenarioSequenceSerializer(many=True, read_only=True)
    quizzes = ARSimulationQuizSerializer(many=True, read_only=True)
    learning_objectives = serializers.SerializerMethodField()
    
    class Meta:
        model = ARSimulationScenario
        fields = [
            'id', 'code', 'title', 'description', 'learning_objectives',
            'scenario_type', 'difficulty', 'duration_minutes', 'immersion_type',
            'initial_panorama_url', 'intro_audio_url', 'intro_audio_duration_seconds',
            'park_location', 'weather_best', 'safety_warning',
            'panoramas', 'sequences', 'quizzes'
        ]
    
    def get_learning_objectives(self, obj):
        """Return objectives based on user's language"""
        objectives = obj.learning_objectives
        request = self.context.get('request')
        lang = 'en'  # Default
        
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            lang = getattr(request.user, 'preferred_language', 'en')
        
        if isinstance(objectives, list):
            return objectives
        
        return objectives.get(lang, objectives.get('en', objectives))


class ARTrainingProgressSerializer(serializers.ModelSerializer):
    """User progress tracking"""
    scenario_details = ARScenarioListSerializer(source='scenario', read_only=True)
    
    class Meta:
        model = ARTrainingProgress
        fields = [
            'id', 'scenario', 'scenario_details', 'panoramas_visited',
            'hotspots_discovered', 'quizzes_completed', 'completion_percentage',
            'is_completed', 'time_spent_seconds', 'started_at',
            'completed_at', 'last_updated'
        ]
        read_only_fields = ['started_at', 'last_updated', 'completed_at']


class ARBadgeSerializer(serializers.ModelSerializer):
    """Achievement badges"""
    class Meta:
        model = ARBadge
        fields = ['id', 'badge_id', 'name', 'description', 'icon_url', 'requirement']
