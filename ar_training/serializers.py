"""
AR Training Serializers
"""
from rest_framework import serializers
from ar_training.models import (
    ARScenario, AREnvironment, ARHotspot, ARQuizQuestion,
    ARTrainingProgress, ARQuizResult, ARBadge, ARUserAchievement,
    ARTrainingStatistics
)


class AREnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AREnvironment
        fields = ['id', 'name', 'description', 'panorama_url', 'thumbnail_url', 'order']


class ARHotspotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ARHotspot
        fields = ['id', 'hotspot_id', 'title', 'position_x', 'position_y', 'content', 'order']


class ARQuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ARQuizQuestion
        fields = ['id', 'question_id', 'question_text', 'options', 'correct_option', 'explanation', 'order']


class ARScenarioListSerializer(serializers.ModelSerializer):
    """Lightweight scenario listing"""
    class Meta:
        model = ARScenario
        fields = ['id', 'code', 'title', 'description', 'scenario_type', 'difficulty', 
                  'duration_minutes', 'thumbnail']


class ARScenarioDetailSerializer(serializers.ModelSerializer):
    """Full scenario with environments and hotspots"""
    environments = AREnvironmentSerializer(many=True, read_only=True)
    hotspots = ARHotspotSerializer(many=True, read_only=True)
    quiz_questions = ARQuizQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = ARScenario
        fields = ['id', 'code', 'title', 'description', 'scenario_type', 'difficulty',
                  'duration_minutes', 'thumbnail', 'is_published', 'environments', 
                  'hotspots', 'quiz_questions']


class ARTrainingProgressSerializer(serializers.ModelSerializer):
    scenario_details = ARScenarioListSerializer(source='scenario', read_only=True)
    
    class Meta:
        model = ARTrainingProgress
        fields = ['id', 'scenario', 'scenario_details', 'visited_hotspots', 'time_spent_seconds',
                  'completion_percentage', 'is_completed', 'started_at', 'last_updated', 'completed_at']
        read_only_fields = ['scenario', 'started_at', 'last_updated', 'completed_at']


class ARQuizResultSerializer(serializers.ModelSerializer):
    scenario_code = serializers.CharField(source='scenario.code', read_only=True)
    
    class Meta:
        model = ARQuizResult
        fields = ['id', 'scenario', 'scenario_code', 'answers', 'score', 'total_questions',
                  'percentage', 'passed', 'time_spent_seconds', 'completed_at']
        read_only_fields = ['score', 'percentage', 'passed', 'completed_at']


class ARBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ARBadge
        fields = ['id', 'badge_id', 'name', 'description', 'icon', 'requirement']


class ARUserAchievementSerializer(serializers.ModelSerializer):
    badge = ARBadgeSerializer(read_only=True)
    
    class Meta:
        model = ARUserAchievement
        fields = ['id', 'badge', 'unlocked_at']


class ARTrainingStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ARTrainingStatistics
        fields = ['total_scenarios_completed', 'total_hotspots_visited', 'average_quiz_score',
                  'total_training_hours', 'current_streak_days', 'longest_streak_days',
                  'last_training_date', 'last_updated']
