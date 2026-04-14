# courses/progress_signals.py
"""
Signals for automatic progress tracking when users complete lessons, practices, and quizzes.
These signals ensure that progress is updated consistently across all models.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Count, Q, Avg, Sum, F
from .models import (
    LessonProgress, ChapterProgress, CourseEnrollment,
    PracticeAttempt, QuizAttempt
)


@receiver(post_save, sender=LessonProgress)
def update_chapter_progress_on_lesson_complete(sender, instance, created, **kwargs):
    """
    Update chapter progress when a lesson is marked complete
    """
    try:
        lesson = instance.lesson
        user = instance.user
        chapter = lesson.chapter
        
        # Get or create chapter progress
        chapter_progress, _ = ChapterProgress.objects.get_or_create(
            user=user,
            chapter=chapter
        )
        
        # Count completed and total lessons
        total_lessons = chapter.lessons.count()
        completed_lessons = LessonProgress.objects.filter(
            user=user,
            lesson__chapter=chapter,
            completed=True
        ).count()
        
        chapter_progress.completed_lessons = completed_lessons
        chapter_progress.total_lessons = total_lessons
        
        # Mark chapter as in-progress when first lesson is completed
        if completed_lessons > 0 and not chapter_progress.started_at:
            chapter_progress.started_at = timezone.now()
        
        # Update progress percentage
        chapter_progress.progress_percentage = chapter_progress.calculate_progress_percentage()
        chapter_progress.save()
        
        # Update course enrollment progress
        update_course_enrollment_progress(user, chapter.course)
        
    except Exception as e:
        print(f"Error updating chapter progress: {e}")


@receiver(post_save, sender=PracticeAttempt)
def update_chapter_progress_on_practice_complete(sender, instance, created, **kwargs):
    """
    Update chapter progress when practice is completed
    """
    try:
        exercise = instance.exercise
        user = instance.user
        chapter = exercise.chapter
        
        # Get or create chapter progress
        chapter_progress, _ = ChapterProgress.objects.get_or_create(
            user=user,
            chapter=chapter
        )
        
        # Get best practice attempt
        best_attempt = PracticeAttempt.objects.filter(
            user=user,
            exercise__chapter=chapter
        ).order_by('-score').first()
        
        if best_attempt:
            chapter_progress.practice_completed = True
            chapter_progress.practice_score = best_attempt.score
            chapter_progress.practice_passed = best_attempt.passed
            chapter_progress.practice_attempts = PracticeAttempt.objects.filter(
                user=user,
                exercise__chapter=chapter
            ).count()
        
        # Update progress percentage
        chapter_progress.progress_percentage = chapter_progress.calculate_progress_percentage()
        chapter_progress.save()
        
        # Update course enrollment progress
        update_course_enrollment_progress(user, chapter.course)
        
    except Exception as e:
        print(f"Error updating chapter progress on practice: {e}")


@receiver(post_save, sender=QuizAttempt)
def update_chapter_progress_on_quiz_complete(sender, instance, created, **kwargs):
    """
    Update chapter progress when quiz is completed
    """
    try:
        quiz = instance.quiz
        user = instance.user
        chapter = quiz.chapter
        
        # Get or create chapter progress
        chapter_progress, _ = ChapterProgress.objects.get_or_create(
            user=user,
            chapter=chapter
        )
        
        # Get best quiz attempt
        best_attempt = QuizAttempt.objects.filter(
            user=user,
            quiz__chapter=chapter
        ).order_by('-score').first()
        
        if best_attempt:
            chapter_progress.quiz_completed = True
            chapter_progress.quiz_score = best_attempt.score
            chapter_progress.quiz_passed = best_attempt.passed
            chapter_progress.quiz_attempts = QuizAttempt.objects.filter(
                user=user,
                quiz__chapter=chapter
            ).count()
            
            # Mark chapter as complete if all requirements met
            if (chapter_progress.completed_lessons == chapter_progress.total_lessons and
                best_attempt.passed):
                chapter_progress.is_complete = True
                chapter_progress.completed_at = timezone.now()
        
        # Update progress percentage
        chapter_progress.progress_percentage = chapter_progress.calculate_progress_percentage()
        chapter_progress.save()
        
        # Update course enrollment progress
        update_course_enrollment_progress(user, chapter.course)
        
    except Exception as e:
        print(f"Error updating chapter progress on quiz: {e}")


def update_course_enrollment_progress(user, course):
    """
    Update course enrollment progress based on chapter completion
    """
    try:
        enrollment, _ = CourseEnrollment.objects.get_or_create(
            user=user,
            course=course
        )
        
        # Mark as in progress if not already
        if enrollment.status == 'enrolled':
            enrollment.status = 'in_progress'
            if not enrollment.started_date:
                enrollment.started_date = timezone.now()
        
        # Count completed and total chapters
        total_chapters = course.chapters.count()
        completed_chapters = ChapterProgress.objects.filter(
            user=user,
            chapter__course=course,
            is_complete=True
        ).count()
        
        enrollment.completed_chapters = completed_chapters
        enrollment.total_chapters = total_chapters
        
        # Calculate overall progress
        if total_chapters > 0:
            # Get all chapter progress to calculate weighted average
            chapter_progresses = ChapterProgress.objects.filter(
                user=user,
                chapter__course=course
            )
            
            if chapter_progresses.exists():
                avg_progress = chapter_progresses.aggregate(
                    avg=Avg('progress_percentage')
                )['avg'] or 0
                enrollment.progress_percentage = min(100, max(0, avg_progress))
            else:
                enrollment.progress_percentage = 0
        
        # Mark course as completed if all chapters done
        if completed_chapters == total_chapters and total_chapters > 0:
            enrollment.status = 'completed'
            enrollment.completed_date = timezone.now()
            
            # Calculate final score as average of chapter quiz scores
            quiz_scores = ChapterProgress.objects.filter(
                user=user,
                chapter__course=course,
                quiz_score__isnull=False
            ).values_list('quiz_score', flat=True)
            
            if quiz_scores:
                enrollment.final_score = sum(quiz_scores) / len(quiz_scores)
        
        enrollment.updated_at = timezone.now()
        enrollment.save()
        
    except Exception as e:
        print(f"Error updating course enrollment progress: {e}")
