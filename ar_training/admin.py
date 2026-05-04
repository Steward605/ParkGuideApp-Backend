"""
AR Training admin configuration.
"""
from django.contrib import admin

from ar_training.models import (
    AR360Panorama,
    ARBadge,
    ARInteractiveHotspot,
    ARQuizAttempt,
    ARScenarioSequence,
    ARSimulationQuiz,
    ARSimulationScenario,
    ARTrainingProgress,
    ARTrainingStatistics,
    ARUserAchievement,
)


@admin.register(ARSimulationScenario)
class ARSimulationScenarioAdmin(admin.ModelAdmin):
    list_display = ("code", "scenario_type", "difficulty", "immersion_type", "is_published", "order")
    list_filter = ("scenario_type", "difficulty", "immersion_type", "is_published")
    search_fields = ("code", "park_location")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("order", "code")


@admin.register(AR360Panorama)
class AR360PanoramaAdmin(admin.ModelAdmin):
    list_display = ("name", "scenario", "order", "is_key_view")
    list_filter = ("scenario__scenario_type", "is_key_view")
    search_fields = ("name", "scenario__code")
    ordering = ("scenario", "order")


@admin.register(ARInteractiveHotspot)
class ARInteractiveHotspotAdmin(admin.ModelAdmin):
    list_display = ("hotspot_id", "scenario", "panorama", "interaction_type", "required_visit", "order")
    list_filter = ("scenario__scenario_type", "interaction_type", "required_visit")
    search_fields = ("hotspot_id", "scenario__code")
    ordering = ("scenario", "panorama", "order")


@admin.register(ARScenarioSequence)
class ARScenarioSequenceAdmin(admin.ModelAdmin):
    list_display = ("scenario", "step_number", "panorama", "recommended_time_seconds")
    list_filter = ("scenario__scenario_type",)
    search_fields = ("scenario__code", "panorama__name")
    ordering = ("scenario", "step_number")


@admin.register(ARSimulationQuiz)
class ARSimulationQuizAdmin(admin.ModelAdmin):
    list_display = ("question_id", "scenario", "difficulty_level", "order", "time_limit_seconds")
    list_filter = ("scenario__scenario_type", "difficulty_level")
    search_fields = ("question_id", "scenario__code")
    ordering = ("scenario", "order")


@admin.register(ARTrainingProgress)
class ARTrainingProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "scenario", "completion_percentage", "is_completed", "started_at")
    list_filter = ("scenario__scenario_type", "is_completed")
    search_fields = ("user__email", "scenario__code")
    readonly_fields = ("started_at", "last_updated", "completed_at")
    ordering = ("-started_at",)


@admin.register(ARQuizAttempt)
class ARQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "quiz", "is_correct", "time_taken_seconds", "completed_at")
    list_filter = ("is_correct", "completed_at", "quiz__scenario__scenario_type")
    search_fields = ("user__email", "quiz__question_id")
    readonly_fields = ("completed_at",)
    ordering = ("-completed_at",)


@admin.register(ARBadge)
class ARBadgeAdmin(admin.ModelAdmin):
    list_display = ("badge_id", "requirement")
    search_fields = ("badge_id",)


@admin.register(ARUserAchievement)
class ARUserAchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "unlocked_at")
    list_filter = ("badge__badge_id", "unlocked_at")
    search_fields = ("user__email", "badge__badge_id")
    ordering = ("-unlocked_at",)


@admin.register(ARTrainingStatistics)
class ARTrainingStatisticsAdmin(admin.ModelAdmin):
    list_display = ("user", "total_scenarios_completed", "average_quiz_score", "total_training_minutes")
    search_fields = ("user__email",)
    readonly_fields = ("last_updated",)
