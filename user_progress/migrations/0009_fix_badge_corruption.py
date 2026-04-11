"""
Migration to fix badge corruption caused by Migration 0004.
This resets all incorrectly granted badges to their proper state based on actual requirements.
"""
from django.db import migrations
from django.db.models import Count, Q


def reset_corrupted_badges(apps, schema_editor):
    """
    Reset all badges that were incorrectly granted by migration 0004.
    Properly evaluate each badge based on actual user progress.
    """
    UserBadge = apps.get_model('user_progress', 'UserBadge')
    Badge = apps.get_model('user_progress', 'Badge')
    ModuleProgress = apps.get_model('courses', 'ModuleProgress')
    
    # First, get all non-major badges that are currently marked as granted
    granted_badges = UserBadge.objects.filter(
        status='granted',
        badge__is_major_badge=False,
    ).select_related('user', 'badge')
    
    for user_badge in granted_badges:
        badge = user_badge.badge
        user = user_badge.user
        
        # Check actual progress for this user
        if badge.course_id:
            # Count modules completed in the specific course
            completed_count = ModuleProgress.objects.filter(
                user=user,
                completed=True,
                module__course=badge.course,
            ).count()
        else:
            # Count all completed modules
            completed_count = ModuleProgress.objects.filter(
                user=user,
                completed=True,
            ).count()
        
        # Determine correct status based on actual progress
        if completed_count >= badge.required_completed_modules:
            # User IS eligible - but reset to PENDING for manual approval
            # (unless auto_approve_when_eligible is True)
            correct_status = 'granted' if badge.auto_approve_when_eligible else 'pending'
        else:
            # User is NOT eligible - reset to IN_PROGRESS
            correct_status = 'in_progress'
        
        # Only update if the status is wrong
        if user_badge.status != correct_status:
            user_badge.status = correct_status
            # Clear award info since we're resetting
            if correct_status == 'in_progress':
                user_badge.is_awarded = False
                user_badge.awarded_by = None
                user_badge.revoked_at = None
                user_badge.revoked_by = None
            user_badge.save(update_fields=[
                'status', 'is_awarded', 'awarded_by', 'revoked_at', 'revoked_by'
            ])
    
    # Handle major badges - reset all to IN_PROGRESS for now
    # They will be re-evaluated properly once regular badges are fixed
    major_badges = UserBadge.objects.filter(
        badge__is_major_badge=True
    ).exclude(
        status='in_progress'
    )
    
    for user_badge in major_badges:
        user_badge.status = 'in_progress'
        user_badge.is_awarded = False
        user_badge.awarded_by = None
        user_badge.revoked_at = None
        user_badge.revoked_by = None
        user_badge.save(update_fields=[
            'status', 'is_awarded', 'awarded_by', 'revoked_at', 'revoked_by'
        ])


def reverse_fix(apps, schema_editor):
    """This migration cannot be safely reversed as it fixes corrupted data."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('user_progress', '0006_badge_progress_and_major_badges'),
    ]

    operations = [
        migrations.RunPython(reset_corrupted_badges, reverse_fix),
    ]
