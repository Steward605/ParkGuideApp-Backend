"""
Management command to initialize the new badge system.
Clears existing badges and creates course completion badges + achievement badges.
"""
from django.core.management.base import BaseCommand
from user_progress.models import Badge, UserBadge
from courses.models import Course


class Command(BaseCommand):
    help = 'Initialize the new badge system with course completion badges and achievement badges'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing badges before creating new ones',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing badges...'))
            UserBadge.objects.all().delete()
            Badge.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Cleared all badges'))

        self.stdout.write(self.style.SUCCESS('Creating new badge system...'))
        
        # 1. Create course completion badges
        courses = Course.objects.all()
        course_badges = {}
        for course in courses:
            badge_name = f"{course.code} Master"
            badge, created = Badge.objects.get_or_create(
                name=badge_name,
                defaults={
                    'description': f'Completed the {course.title.get("en", "Course")} course ({course.code})',
                    'course': course,
                    'is_major_badge': False,
                    'required_completed_modules': 1,
                    'auto_approve_when_eligible': True,
                    'is_active': True,
                }
            )
            course_badges[course.id] = badge
            status = '✓ Created' if created else '→ Already exists'
            self.stdout.write(f'  {status}: {badge_name}')

        # 2. Create achievement/milestone badges
        achievement_badges = [
            {
                'name': 'Course Veteran',
                'description': 'Completed 3 courses',
                'required_badges_count': 3,
                'is_major_badge': True,
            },
            {
                'name': 'Course Master',
                'description': 'Completed 5 courses',
                'required_badges_count': 5,
                'is_major_badge': True,
            },
            {
                'name': 'Learning Champion',
                'description': 'Completed 10 courses',
                'required_badges_count': 10,
                'is_major_badge': True,
            },
            {
                'name': 'Expert Tracker',
                'description': 'Completed all available courses',
                'required_badges_count': len(list(courses)),
                'is_major_badge': True,
            },
        ]

        for badge_config in achievement_badges:
            badge, created = Badge.objects.get_or_create(
                name=badge_config['name'],
                defaults={
                    'description': badge_config['description'],
                    'is_major_badge': True,
                    'required_badges_count': badge_config['required_badges_count'],
                    'auto_approve_when_eligible': True,
                    'is_active': True,
                }
            )
            status = '✓ Created' if created else '→ Already exists'
            self.stdout.write(f'  {status}: {badge["name"]} (requires {badge_config["required_badges_count"]} course badges)')

        self.stdout.write(self.style.SUCCESS('\n✓ Badge system initialized successfully!'))
        self.stdout.write(f'  • {len(list(courses))} course badges')
        self.stdout.write(f'  • {len(achievement_badges)} achievement badges')
        self.stdout.write(f'  • Total: {len(list(courses)) + len(achievement_badges)} badges')
