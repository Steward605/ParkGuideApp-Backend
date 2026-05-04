"""
AR Training URL routing.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ar_training.views import (
    AR360PanoramaViewSet,
    ARBadgeViewSet,
    ARInteractiveHotspotViewSet,
    ARScenarioSequenceViewSet,
    ARSimulationQuizViewSet,
    ARSimulationScenarioViewSet,
    ARStatisticsViewSet,
    ARTrainingProgressViewSet,
)


router = DefaultRouter()
router.register(r"scenarios", ARSimulationScenarioViewSet, basename="ar-scenario")
router.register(r"panoramas", AR360PanoramaViewSet, basename="ar-panorama")
router.register(r"hotspots", ARInteractiveHotspotViewSet, basename="ar-hotspot")
router.register(r"sequences", ARScenarioSequenceViewSet, basename="ar-sequence")
router.register(r"quiz", ARSimulationQuizViewSet, basename="ar-quiz")
router.register(r"progress", ARTrainingProgressViewSet, basename="ar-progress")
router.register(r"badges", ARBadgeViewSet, basename="ar-badge")
router.register(r"statistics", ARStatisticsViewSet, basename="ar-statistics")

urlpatterns = [
    path("", include(router.urls)),
]
