# courses/dashboard_serializers.py
"""
Dashboard-specific serializers for user progress tracking and course management
These serializers are designed for dashboard views, aggregating data for easy user tracking.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Avg, Sum, F
from .models import (
    Course, Chapter, Lesson, Quiz, PracticeExercise,
    CourseEnrollment, ChapterProgress, LessonProgress,
    PracticeAttempt, QuizAttempt
)

User = get_user_model()


# ============================================================================
# USER PROGRESS SUMMARY SERIALIZERS
# ============================================================================

class UserProgressSummarySerializer(serializers.Serializer):
    """
    Summary of a user's overall learning progress
    """
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    username = serializers.CharField()
    
    total_courses_enrolled = serializers.IntegerField()
    total_courses_completed = serializers.IntegerField()
    total_chapters_completed = serializers.IntegerField()
    total_lessons_completed = serializers.IntegerField()
    total_quizzes_passed = serializers.IntegerField()
    
    average_course_progress = serializers.FloatField()
    average_course_score = serializers.FloatField()
    
    total_learning_time = serializers.IntegerField()  # in seconds
    

class CourseProgressDetailSerializer(serializers.ModelSerializer):
    """
    Detailed progress for a single course enrollment
    """
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    chapters_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'course_code', 'course_title', 'status',
            'progress_percentage', 'final_score',
            'enrollment_date', 'started_date', 'completed_date',
            'completed_chapters', 'total_chapters',
            'total_time_spent', 'chapters_detail'
        ]
    
    def get_chapters_detail(self, obj):
        """Get detailed progress for each chapter"""
        chapters = ChapterProgress.objects.filter(
            user=obj.user,
            chapter__course=obj.course
        ).order_by('chapter__order')
        
        return [
            {
                'chapter_id': cp.chapter.id,
                'chapter_title': cp.chapter.title.get('en', 'Untitled') if isinstance(cp.chapter.title, dict) else str(cp.chapter.title),
                'order': cp.chapter.order,
                'lessons_completed': cp.completed_lessons,
                'total_lessons': cp.total_lessons,
                'practice_score': cp.practice_score,
                'practice_passed': cp.practice_passed,
                'quiz_score': cp.quiz_score,
                'quiz_passed': cp.quiz_passed,
                'progress_percentage': cp.progress_percentage,
                'is_complete': cp.is_complete,
                'started_at': cp.started_at,
                'completed_at': cp.completed_at,
            }
            for cp in chapters
        ]


class ChapterProgressDetailSerializer(serializers.ModelSerializer):
    """
    Detailed progress for a single chapter
    """
    chapter_title = serializers.CharField(source='chapter.title', read_only=True)
    chapter_order = serializers.IntegerField(source='chapter.order', read_only=True)
    course_title = serializers.CharField(source='chapter.course.title', read_only=True)
    course_code = serializers.CharField(source='chapter.course.code', read_only=True)
    
    lessons_detail = serializers.SerializerMethodField()
    practice_detail = serializers.SerializerMethodField()
    quiz_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = ChapterProgress
        fields = [
            'id', 'chapter_title', 'chapter_order', 'course_title', 'course_code',
            'completed_lessons', 'total_lessons',
            'practice_completed', 'practice_score', 'practice_attempts',
            'quiz_completed', 'quiz_score', 'quiz_attempts',
            'progress_percentage', 'is_complete',
            'started_at', 'completed_at',
            'lessons_detail', 'practice_detail', 'quiz_detail'
        ]
    
    def get_lessons_detail(self, obj):
        """Get lesson completion details"""
        lessons = LessonProgress.objects.filter(
            user=obj.user,
            lesson__chapter=obj.chapter
        ).order_by('lesson__order')
        
        return [
            {
                'lesson_id': lp.lesson.id,
                'title': lp.lesson.title.get('en', 'Untitled') if isinstance(lp.lesson.title, dict) else str(lp.lesson.title),
                'order': lp.lesson.order,
                'completed': lp.completed,
                'time_spent': lp.time_spent,
                'last_viewed': lp.last_viewed,
                'completed_at': lp.completed_at,
            }
            for lp in lessons
        ]
    
    def get_practice_detail(self, obj):
        """Get practice attempt details"""
        practices = PracticeAttempt.objects.filter(
            user=obj.user,
            exercise__chapter=obj.chapter
        ).order_by('-completed_at')
        
        return [
            {
                'exercise_id': pa.exercise.id,
                'title': pa.exercise.title.get('en', 'Untitled') if isinstance(pa.exercise.title, dict) else str(pa.exercise.title),
                'attempt_number': pa.attempt_number,
                'score': pa.score,
                'passed': pa.passed,
                'attempted_at': pa.attempted_at,
            }
            for pa in practices[:5]  # Last 5 attempts
        ]
    
    def get_quiz_detail(self, obj):
        """Get quiz attempt details"""
        quizzes = QuizAttempt.objects.filter(
            user=obj.user,
            quiz__chapter=obj.chapter
        ).order_by('-completed_at')
        
        return [
            {
                'quiz_id': qa.quiz.id,
                'title': qa.quiz.title.get('en', 'Untitled') if isinstance(qa.quiz.title, dict) else str(qa.quiz.title),
                'attempt_number': qa.attempt_number,
                'score': qa.score,
                'passed': qa.passed,
                'time_spent': qa.time_spent,
                'started_at': qa.started_at,
                'completed_at': qa.completed_at,
            }
            for qa in quizzes[:5]  # Last 5 attempts
        ]


# ============================================================================
# DASHBOARD STATISTICS SERIALIZERS
# ============================================================================

class CourseCatalogStatsSerializer(serializers.Serializer):
    """
    Statistics about course catalog
    """
    total_courses = serializers.IntegerField()
    published_courses = serializers.IntegerField()
    total_chapters = serializers.IntegerField()
    total_lessons = serializers.IntegerField()
    total_quizzes = serializers.IntegerField()


class UserLearningStatsSerializer(serializers.Serializer):
    """
    Learning statistics for a single user
    """
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    
    courses_enrolled = serializers.IntegerField()
    courses_in_progress = serializers.IntegerField()
    courses_completed = serializers.IntegerField()
    courses_failed = serializers.IntegerField()
    
    chapters_completed = serializers.IntegerField()
    lessons_completed = serializers.IntegerField()
    quizzes_passed = serializers.IntegerField()
    quizzes_failed = serializers.IntegerField()
    
    average_quiz_score = serializers.FloatField()
    total_time_spent_seconds = serializers.IntegerField()
    
    badges_earned = serializers.IntegerField()


class DashboardOverviewSerializer(serializers.Serializer):
    """
    Overall dashboard overview with system and user statistics
    """
    catalog_stats = CourseCatalogStatsSerializer()
    user_count = serializers.IntegerField()
    active_users_this_week = serializers.IntegerField()
    total_enrollments = serializers.IntegerField()
    active_enrollments = serializers.IntegerField()
    completed_enrollments = serializers.IntegerField()


# ============================================================================
# LEADERBOARD SERIALIZERS
# ============================================================================

class UserLeaderboardEntry(serializers.Serializer):
    """
    Single user entry in leaderboard
    """
    rank = serializers.IntegerField()
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    username = serializers.CharField()
    
    courses_completed = serializers.IntegerField()
    quizzes_passed = serializers.IntegerField()
    average_score = serializers.FloatField()
    total_learning_time = serializers.IntegerField()
    badges_earned = serializers.IntegerField()
    
    last_activity = serializers.DateTimeField()
