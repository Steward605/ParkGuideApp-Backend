from django.contrib import admin

from ar_training.models import ARHotspot, ARPanorama, ARQuizQuestion, ARScenario, ARTrainingProgress


@admin.register(ARScenario)
class ARScenarioAdmin(admin.ModelAdmin):
    list_display = ("code", "scenario_type", "difficulty", "is_published", "order")
    list_filter = ("scenario_type", "difficulty", "is_published")
    search_fields = ("code",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("order", "code")


@admin.register(ARPanorama)
class ARPanoramaAdmin(admin.ModelAdmin):
    list_display = ("name", "scenario", "order")
    list_filter = ("scenario__scenario_type",)
    search_fields = ("name", "scenario__code")
    ordering = ("scenario", "order")


@admin.register(ARHotspot)
class ARHotspotAdmin(admin.ModelAdmin):
    list_display = ("hotspot_id", "panorama", "icon_type", "order")
    list_filter = ("panorama__scenario__scenario_type", "icon_type")
    search_fields = ("hotspot_id", "panorama__name", "panorama__scenario__code")
    ordering = ("panorama", "order")


@admin.register(ARQuizQuestion)
class ARQuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("scenario", "order", "correct_option_index")
    list_filter = ("scenario__scenario_type",)
    search_fields = ("scenario__code",)
    ordering = ("scenario", "order")


@admin.register(ARTrainingProgress)
class ARTrainingProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "scenario", "completion_percentage", "best_score", "is_completed", "started_at")
    list_filter = ("scenario__scenario_type", "is_completed")
    search_fields = ("user__email", "user__username", "scenario__code")
    readonly_fields = ("started_at", "completed_at", "updated_at")
    ordering = ("-updated_at",)
