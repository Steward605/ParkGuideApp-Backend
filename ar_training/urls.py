"""
AR Training URL routing
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ar_training.views import (
    ARScenarioViewSet,
    AREnvironmentViewSet,
    ARHotspotViewSet,
    ARTrainingProgressViewSet,
    ARQuizViewSet,
    ARQuizResultViewSet,
    ARBadgeViewSet,
    ARUserAchievementViewSet,
    ARStatisticsViewSet,
)

router = DefaultRouter()
router.register(r'scenarios', ARScenarioViewSet, basename='ar-scenario')
router.register(r'environments', AREnvironmentViewSet, basename='ar-environment')
router.register(r'hotspots', ARHotspotViewSet, basename='ar-hotspot')
router.register(r'progress', ARTrainingProgressViewSet, basename='ar-progress')
router.register(r'quiz', ARQuizViewSet, basename='ar-quiz')
router.register(r'quiz-results', ARQuizResultViewSet, basename='ar-quiz-result')
router.register(r'badges', ARBadgeViewSet, basename='ar-badge')
router.register(r'achievements', ARUserAchievementViewSet, basename='ar-achievement')
router.register(r'statistics', ARStatisticsViewSet, basename='ar-statistics')

urlpatterns = [
    path('', include(router.urls)),
]
