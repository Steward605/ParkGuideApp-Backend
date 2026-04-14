"""
Clean, fresh URL routing for courses API
Simplified routing using DefaultRouter
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from courses.views_fresh import (
    CourseViewSet,
    CourseEnrollmentViewSet,
    ChapterViewSet,
    LessonViewSet,
    PracticeExerciseViewSet,
    QuizViewSet,
)

# Create router and register all viewsets
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'enrollments', CourseEnrollmentViewSet, basename='enrollment')
router.register(r'chapters', ChapterViewSet, basename='chapter')
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'practice', PracticeExerciseViewSet, basename='practice')
router.register(r'quizzes', QuizViewSet, basename='quiz')

# Router generates these URLs:
# Courses:
#   GET    /api/courses/                      - List courses
#   POST   /api/courses/                      - Create course
#   GET    /api/courses/{id}/                 - Get course details
#   PUT    /api/courses/{id}/                 - Update course
#   PATCH  /api/courses/{id}/                 - Partial update course
#   DELETE /api/courses/{id}/                 - Delete course
#   POST   /api/courses/{id}/enroll/          - Enroll user
#
# Chapters:
#   GET    /api/chapters/                     - List chapters
#   POST   /api/chapters/                     - Create chapter
#   GET    /api/chapters/{id}/                - Get chapter details
#   PUT    /api/chapters/{id}/                - Update chapter
#   PATCH  /api/chapters/{id}/                - Partial update chapter
#   DELETE /api/chapters/{id}/                - Delete chapter
#
# And similar for lessons, practice, quizzes

urlpatterns = [
    path('', include(router.urls)),
]
