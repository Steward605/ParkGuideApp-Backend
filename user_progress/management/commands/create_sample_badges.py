"""
Management command to create sample badges for the course completion system.
"""
from django.core.management.base import BaseCommand
from user_progress.models import Badge
from courses.models import Course


class Command(BaseCommand):
    help = 'Create sample badges for courses'

    def handle(self, *args, **options):
        """Create course completion and achievement badges."""
        
        # Get all courses
        courses = Course.objects.all()
        
        # Create course completion badges (one per course)
        # These badges require admin approval when granted
        course_badges_created = 0
        course_badges_updated = 0
        for course in courses:
            badge_name = f"{course.code} Master"
            try:
                badge = Badge.objects.get(name=badge_name)
                # Badge exists, update it
                if badge.course_id != course.id or badge.auto_approve_when_eligible != False:
                    badge.course = course
                    badge.auto_approve_when_eligible = False
                    badge.is_major_badge = False
                    badge.save()
                    course_badges_updated += 1
                    self.stdout.write(self.style.WARNING(f'✓ Updated badge: {badge_name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'✓ Badge already correct: {badge_name}'))
            except Badge.DoesNotExist:
                # Create new badge
                badge = Badge.objects.create(
                    name=badge_name,
                    description=f'Completed the {course.title.get("en", "Course")} course ({course.code})',
                    course=course,
                    required_completed_modules=1,
                    auto_approve_when_eligible=False,  # Requires admin approval
                    is_active=True,
                    is_major_badge=False,
                )
                course_badges_created += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created badge: {badge_name}'))
        
        # Create achievement/milestone badges (auto-approved when eligible)
        # These are major badges that don't require admin approval
        achievement_badges_data = [
            {
                'name': 'Emerging Explorer',
                'description': 'Completed your first course! Welcome to the journey of learning.',
                'required_badges_count': 1,
            },
            {
                'name': 'Steady Learner',
                'description': 'Completed 2 courses. You\'re building momentum!',
                'required_badges_count': 2,
            },
            {
                'name': 'Park Master',
                'description': 'Completed 3 courses. You\'re a true park expert!',
                'required_badges_count': 3,
            },
            {
                'name': 'Natural Explorer',
                'description': 'Completed 4 courses. Your knowledge of nature is amazing!',
                'required_badges_count': 4,
            },
            {
                'name': 'Dedicated Scholar',
                'description': 'Completed 5 courses. Your dedication is inspiring!',
                'required_badges_count': 5,
            },
            {
                'name': 'Knowledge Collector',
                'description': 'Completed 7 courses. You\'ve mastered extensive material!',
                'required_badges_count': 7,
            },
            {
                'name': 'Ultimate Park Guide',
                'description': 'Completed all courses! You\'re the ultimate park guide authority!',
                'required_badges_count': 10,
            },
        ]
        
        achievement_badges_created = 0
        achievement_badges_updated = 0
        for badge_data in achievement_badges_data:
            badge_name = badge_data['name']
            try:
                badge = Badge.objects.get(name=badge_name)
                # Badge exists, update it
                if not badge.auto_approve_when_eligible or badge.is_major_badge != True:
                    badge.auto_approve_when_eligible = True
                    badge.is_major_badge = True
                    badge.save()
                    achievement_badges_updated += 1
                    self.stdout.write(self.style.WARNING(f'✓ Updated achievement badge: {badge_name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'✓ Achievement badge already correct: {badge_name}'))
            except Badge.DoesNotExist:
                # Create new achievement badge
                badge = Badge.objects.create(
                    name=badge_data['name'],
                    description=badge_data['description'],
                    required_badges_count=badge_data['required_badges_count'],
                    auto_approve_when_eligible=True,  # Auto-grant these
                    is_active=True,
                    is_major_badge=True,
                    course=None,  # Achievement badges are not tied to specific courses
                )
                achievement_badges_created += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created achievement badge: {badge_name}'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Complete! Created {course_badges_created} course badges '
                f'and {achievement_badges_created} achievement badges. '
                f'Updated {course_badges_updated + achievement_badges_updated} existing badges.'
            )
        )
