from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import (
    CourseEnrollment, Chapter, Lesson, 
    ChapterProgress, LessonProgress
)


@receiver(post_save, sender=CourseEnrollment)
def initialize_progress_on_enrollment(sender, instance, created, **kwargs):
    """
    When a user enrolls in a course, create progress tracking records
    for all chapters and lessons in the course.
    """
    if not created:
        # Only initialize on first creation, not on updates
        return
    
    course = instance.course
    user = instance.user
    
    # For each chapter in the course
    for chapter in course.chapters.all():
        # Create ChapterProgress record
        chapter_progress, _ = ChapterProgress.objects.get_or_create(
            user=user,
            chapter=chapter,
            defaults={
                'total_lessons': chapter.lessons.count(),
                'completed_lessons': 0,
                'progress_percentage': 0,
                'is_complete': False,
            }
        )
        
        # For each lesson in the chapter, create LessonProgress records
        for lesson in chapter.lessons.all():
            LessonProgress.objects.get_or_create(
                user=user,
                lesson=lesson,
                defaults={
                    'completed': False,
                    'time_spent': 0,
                }
            )
    
    print(f"✅ Progress records initialized for {user.username} in course {course.code}")


@receiver(post_save, sender=CourseEnrollment)
def auto_grant_completion_badge(sender, instance, created, update_fields, **kwargs):
    """
    When a course enrollment is marked as completed, automatically grant the course badge.
    Checks for achievement badges as well.
    """
    if created:
        # Only process on updates, not on creation
        return
    
    # Check if status changed to completed
    if instance.status == 'completed' and (not update_fields or 'status' in update_fields):
        from user_progress.services import grant_course_completion_badge
        
        grant_course_completion_badge(instance.user, instance.course)
        print(f"✅ Badge granted for course completion: {instance.user.username} → {instance.course.code}")
