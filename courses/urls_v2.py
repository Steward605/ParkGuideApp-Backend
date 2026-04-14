# Complete rewrite - Simplified multi-language URLs
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views_v2 import (
    CourseViewSet, ChapterViewSet, LessonViewSet,
    PracticeExerciseViewSet, QuizViewSet
)

# Create router and register viewsets
router = SimpleRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'chapters', ChapterViewSet, basename='chapter')
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'practice-exercises', PracticeExerciseViewSet, basename='practiceexercise')
router.register(r'quizzes', QuizViewSet, basename='quiz')

# Include router URLs
urlpatterns = [
    path('', include(router.urls)),
]
