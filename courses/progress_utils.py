# courses/progress_utils.py
"""
Utility functions for progress calculation, tracking, and bulk operations
These can be used for manual updates, migrations, and batch operations.
"""

from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from .models import (
    CourseEnrollment, ChapterProgress, LessonProgress,
    PracticeAttempt, QuizAttempt, Course, Chapter
)


def recalculate_all_user_progress(user):
    """
    Recalculate all progress for a specific user
    Useful for data consistency checks and after migrations
    """
    enrollments = CourseEnrollment.objects.filter(user=user)
    
    for enrollment in enrollments:
        recalculate_course_enrollment_progress(enrollment)


def recalculate_course_enrollment_progress(enrollment):
    """
    Recalculate progress for a specific course enrollment
    """
    user = enrollment.user
    course = enrollment.course
    
    # Count chapters
    total_chapters = course.chapters.count()
    
    # Count completed chapters
    completed_chapters = ChapterProgress.objects.filter(
        user=user,
        chapter__course=course,
        is_complete=True
    ).count()
    
    # Get all chapter progress to calculate weighted average
    chapter_progresses = ChapterProgress.objects.filter(
        user=user,
        chapter__course=course
    )
    
    if chapter_progresses.exists():
        avg_progress = chapter_progresses.aggregate(avg=Avg('progress_percentage'))['avg'] or 0
        progress_percentage = min(100, max(0, avg_progress))
    else:
        progress_percentage = 0
    
    # Update enrollment
    enrollment.completed_chapters = completed_chapters
    enrollment.total_chapters = total_chapters
    enrollment.progress_percentage = progress_percentage
    
    # Calculate final score as average of chapter quiz scores
    quiz_scores = ChapterProgress.objects.filter(
        user=user,
        chapter__course=course,
        quiz_score__isnull=False
    ).values_list('quiz_score', flat=True)
    
    if quiz_scores:
        enrollment.final_score = sum(quiz_scores) / len(quiz_scores)
    
    # Update status based on completion
    if completed_chapters == total_chapters and total_chapters > 0:
        if enrollment.status != 'completed':
            enrollment.status = 'completed'
            enrollment.completed_date = timezone.now()
    elif completed_chapters > 0:
        if enrollment.status == 'enrolled':
            enrollment.status = 'in_progress'
            enrollment.started_date = timezone.now()
    
    enrollment.updated_at = timezone.now()
    enrollment.save()


def recalculate_chapter_progress(chapter_progress):
    """
    Recalculate progress for a specific chapter
    """
    user = chapter_progress.user
    chapter = chapter_progress.chapter
    
    # Count lessons
    total_lessons = chapter.lessons.count()
    completed_lessons = LessonProgress.objects.filter(
        user=user,
        lesson__chapter=chapter,
        completed=True
    ).count()
    
    chapter_progress.completed_lessons = completed_lessons
    chapter_progress.total_lessons = total_lessons
    
    # Get best practice score
    best_practice = PracticeAttempt.objects.filter(
        user=user,
        exercise__chapter=chapter
    ).order_by('-score').first()
    
    if best_practice:
        chapter_progress.practice_completed = True
        chapter_progress.practice_score = best_practice.score
        chapter_progress.practice_passed = best_practice.passed
    
    # Get best quiz score
    best_quiz = QuizAttempt.objects.filter(
        user=user,
        quiz__chapter=chapter
    ).order_by('-score').first()
    
    if best_quiz:
        chapter_progress.quiz_completed = True
        chapter_progress.quiz_score = best_quiz.score
        chapter_progress.quiz_passed = best_quiz.passed
    
    # Check if chapter is complete
    if (completed_lessons == total_lessons and total_lessons > 0 and
        chapter_progress.quiz_passed):
        chapter_progress.is_complete = True
        if not chapter_progress.completed_at:
            chapter_progress.completed_at = timezone.now()
    
    # Calculate progress percentage
    chapter_progress.progress_percentage = chapter_progress.calculate_progress_percentage()
    chapter_progress.updated_at = timezone.now()
    chapter_progress.save()


def get_user_learning_time(user, course=None):
    """
    Calculate total learning time for a user (optionally for a specific course)
    Returns time in seconds
    """
    lessons_query = LessonProgress.objects.filter(user=user, completed=True)
    quiz_query = QuizAttempt.objects.filter(user=user, passed=True)
    
    if course:
        lessons_query = lessons_query.filter(lesson__chapter__course=course)
        quiz_query = quiz_query.filter(quiz__chapter__course=course)
    
    lesson_time = lessons_query.aggregate(total=Sum('time_spent'))['total'] or 0
    quiz_time = quiz_query.aggregate(total=Sum('time_spent'))['total'] or 0
    
    return lesson_time + quiz_time


def get_course_statistics(course):
    """
    Get statistics for a course
    """
    enrollments = CourseEnrollment.objects.filter(course=course)
    chapters = course.chapters.all()
    
    return {
        'total_enrollments': enrollments.count(),
        'active_enrollments': enrollments.filter(status__in=['enrolled', 'in_progress']).count(),
        'completed_enrollments': enrollments.filter(status='completed').count(),
        'average_progress': enrollments.aggregate(avg=Avg('progress_percentage'))['avg'] or 0,
        'total_chapters': chapters.count(),
        'total_lessons': sum(chapter.lessons.count() for chapter in chapters),
        'total_quizzes': sum(chapter.quizzes.count() for chapter in chapters),
    }


def get_user_course_statistics(user):
    """
    Get comprehensive statistics for a user
    """
    enrollments = CourseEnrollment.objects.filter(user=user)
    
    courses_enrolled = enrollments.count()
    courses_completed = enrollments.filter(status='completed').count()
    courses_in_progress = enrollments.filter(status='in_progress').count()
    
    lesson_progress = LessonProgress.objects.filter(user=user, completed=True)
    lessons_completed = lesson_progress.count()
    
    quiz_attempts = QuizAttempt.objects.filter(user=user, passed=True)
    quizzes_passed = quiz_attempts.count()
    
    practice_attempts = PracticeAttempt.objects.filter(user=user, passed=True)
    practice_passed = practice_attempts.count()
    
    average_quiz_score = QuizAttempt.objects.filter(user=user).aggregate(
        avg=Avg('score')
    )['avg'] or 0
    
    total_learning_time = get_user_learning_time(user)
    
    return {
        'courses_enrolled': courses_enrolled,
        'courses_completed': courses_completed,
        'courses_in_progress': courses_in_progress,
        'lessons_completed': lessons_completed,
        'quizzes_passed': quizzes_passed,
        'practice_exercises_passed': practice_passed,
        'average_quiz_score': round(average_quiz_score, 2),
        'total_learning_time_seconds': total_learning_time,
        'total_learning_time_hours': round(total_learning_time / 3600, 2),
    }


def bulk_recalculate_progress_for_course(course):
    """
    Recalculate progress for all users in a course
    Use this after data migrations or consistency checks
    """
    enrollments = CourseEnrollment.objects.filter(course=course)
    
    for enrollment in enrollments:
        recalculate_course_enrollment_progress(enrollment)


def get_active_users_in_period(days=7):
    """
    Get users active in the last N days
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    
    return LessonProgress.objects.filter(
        last_viewed__gte=cutoff_date
    ).values_list('user', flat=True).distinct().count()


def get_user_activity_summary(user, days=30):
    """
    Get user activity summary for the last N days
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    
    lessons_viewed = LessonProgress.objects.filter(
        user=user,
        last_viewed__gte=cutoff_date
    ).count()
    
    quizzes_attempted = QuizAttempt.objects.filter(
        user=user,
        started_at__gte=cutoff_date
    ).count()
    
    practice_attempted = PracticeAttempt.objects.filter(
        user=user,
        attempted_at__gte=cutoff_date
    ).count()
    
    total_time = (
        LessonProgress.objects.filter(
            user=user,
            last_viewed__gte=cutoff_date,
            completed=True
        ).aggregate(total=Sum('time_spent'))['total'] or 0
    ) + (
        QuizAttempt.objects.filter(
            user=user,
            started_at__gte=cutoff_date
        ).aggregate(total=Sum('time_spent'))['total'] or 0
    )
    
    return {
        'lessons_viewed': lessons_viewed,
        'quizzes_attempted': quizzes_attempted,
        'practice_attempted': practice_attempted,
        'total_time_seconds': total_time,
        'period_days': days,
    }


def export_user_progress_report(user):
    """
    Generate a comprehensive progress report for export
    """
    from .models import CourseEnrollment, Chapter
    
    enrollments = CourseEnrollment.objects.filter(user=user)
    
    report = {
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username,
        },
        'summary': get_user_course_statistics(user),
        'courses': []
    }
    
    for enrollment in enrollments:
        course_data = {
            'course_id': enrollment.course.id,
            'course_code': enrollment.course.code,
            'status': enrollment.status,
            'progress': enrollment.progress_percentage,
            'score': enrollment.final_score,
            'chapters': []
        }
        
        chapters = ChapterProgress.objects.filter(
            user=user,
            chapter__course=enrollment.course
        )
        
        for chapter_progress in chapters:
            chapter_data = {
                'chapter_id': chapter_progress.chapter.id,
                'title': chapter_progress.chapter.title.get('en', 'Untitled') if isinstance(chapter_progress.chapter.title, dict) else str(chapter_progress.chapter.title),
                'lessons_completed': chapter_progress.completed_lessons,
                'total_lessons': chapter_progress.total_lessons,
                'practice_score': chapter_progress.practice_score,
                'quiz_score': chapter_progress.quiz_score,
                'is_complete': chapter_progress.is_complete,
            }
            course_data['chapters'].append(chapter_data)
        
        report['courses'].append(course_data)
    
    return report
