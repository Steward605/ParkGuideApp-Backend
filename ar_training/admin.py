"""
AR Training Admin Configuration
"""
from django.contrib import admin
from ar_training.models import (
    ARScenario, AREnvironment, ARHotspot, ARQuizQuestion,
    ARTrainingProgress, ARQuizResult, ARBadge, ARUserAchievement,
    ARTrainingStatistics
)


@admin.register(ARScenario)
class ARScenarioAdmin(admin.ModelAdmin):
    list_display = ('code', 'scenario_type', 'difficulty', 'is_published', 'created_at')
    list_filter = ('scenario_type', 'difficulty', 'is_published')
    search_fields = ('code', 'title')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('code', 'title', 'description', 'thumbnail')
        }),
        ('Settings', {
            'fields': ('scenario_type', 'difficulty', 'duration_minutes', 'is_published')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AREnvironment)
class AREnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'scenario', 'order')
    list_filter = ('scenario__scenario_type',)
    search_fields = ('name', 'scenario__code')
    ordering = ('scenario', 'order')


@admin.register(ARHotspot)
class ARHotspotAdmin(admin.ModelAdmin):
    list_display = ('hotspot_id', 'scenario', 'order', 'position_x', 'position_y')
    list_filter = ('scenario__scenario_type',)
    search_fields = ('hotspot_id', 'title')
    ordering = ('scenario', 'order')


@admin.register(ARQuizQuestion)
class ARQuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_id', 'scenario', 'order', 'correct_option')
    list_filter = ('scenario__scenario_type',)
    search_fields = ('question_id', 'scenario__code')
    ordering = ('scenario', 'order')


@admin.register(ARTrainingProgress)
class ARTrainingProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'scenario', 'completion_percentage', 'is_completed', 'started_at')
    list_filter = ('scenario__scenario_type', 'is_completed')
    search_fields = ('user__email', 'scenario__code')
    readonly_fields = ('started_at', 'last_updated', 'completed_at')
    ordering = ('-started_at',)


@admin.register(ARQuizResult)
class ARQuizResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'scenario', 'percentage', 'passed', 'completed_at')
    list_filter = ('scenario__scenario_type', 'passed', 'completed_at')
    search_fields = ('user__email', 'scenario__code')
    readonly_fields = ('completed_at',)
    ordering = ('-completed_at',)


@admin.register(ARBadge)
class ARBadgeAdmin(admin.ModelAdmin):
    list_display = ('badge_id', 'name', 'requirement')
    search_fields = ('badge_id', 'name')


@admin.register(ARUserAchievement)
class ARUserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'unlocked_at')
    list_filter = ('badge__badge_id', 'unlocked_at')
    search_fields = ('user__email', 'badge__badge_id')
    ordering = ('-unlocked_at',)


@admin.register(ARTrainingStatistics)
class ARTrainingStatisticsAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_scenarios_completed', 'average_quiz_score', 'total_training_hours')
    search_fields = ('user__email',)
    readonly_fields = ('last_updated',)
