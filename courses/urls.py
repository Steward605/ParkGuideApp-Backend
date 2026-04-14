from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # New course system
    CourseViewSet, CourseEnrollmentViewSet,
    ChapterViewSet, LessonViewSet,
    PracticeExerciseViewSet, QuizViewSet,
    # Legacy
    ModuleViewSet, ModuleProgressViewSet, CourseProgressViewSet, CompleteModuleView
)
from .dashboard_views import (
    UserProgressViewSet, DashboardStatsView, LeaderboardView
)

# MANUAL ROUTE REGISTRATION - NO DEFAULTS ROUTER FOR CRUD ENDPOINTS
urlpatterns = [
    # ======================================
    # CHAPTERS - Full CRUD with explicit DELETE support
    # ======================================
    path('chapters/', ChapterViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='chapter-list'),
    path('chapters/<int:pk>/', ChapterViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='chapter-detail'),
    
    # ======================================
    # LESSONS - Full CRUD with explicit DELETE support
    # ======================================
    path('lessons/', LessonViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='lesson-list'),
    path('lessons/<int:pk>/', LessonViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='lesson-detail'),
    
    # ======================================
    # QUIZZES - Full CRUD with explicit DELETE support
    # ======================================
    path('quizzes/', QuizViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='quiz-list'),
    path('quizzes/<int:pk>/', QuizViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='quiz-detail'),
    
    # ======================================
    # PRACTICE EXERCISES - Full CRUD with explicit DELETE support
    # ======================================
    path('practice/', PracticeExerciseViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='practice-list'),
    path('practice/<int:pk>/', PracticeExerciseViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='practice-detail'),
]

# Router for remaining endpoints (courses, enrollments, modules, progress)
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'enrollments', CourseEnrollmentViewSet, basename='enrollment')
router.register(r'dashboard/user-progress', UserProgressViewSet, basename='user-progress')
router.register(r'modules', ModuleViewSet, basename='module')
router.register(r'progress', ModuleProgressViewSet, basename='progress')
router.register(r'course-progress', CourseProgressViewSet, basename='course-progress')

# Append router paths AFTER all explicit paths
urlpatterns += [
    path('', include(router.urls)),
    
    path('complete-module/', CompleteModuleView.as_view(), name='complete-module'),
    path('dashboard/stats/overview/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]