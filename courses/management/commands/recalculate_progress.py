#!/usr/bin/env python
# courses/management/commands/recalculate_progress.py
"""
Management command to recalculate user progress
This is useful for data consistency, migrations, or after bulk updates
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import Course, CourseEnrollment
from courses.progress_utils import (
    recalculate_all_user_progress,
    recalculate_course_enrollment_progress,
    bulk_recalculate_progress_for_course,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Recalculate progress for users and courses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=int,
            help='Recalculate progress for specific user ID'
        )
        parser.add_argument(
            '--course',
            type=int,
            help='Recalculate progress for all users in a specific course ID'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Recalculate progress for all users'
        )
        parser.add_argument(
            '--enrollment',
            type=int,
            help='Recalculate progress for specific enrollment ID'
        )

    def handle(self, *args, **options):
        if options.get('user'):
            self.recalculate_user(options['user'])
        elif options.get('course'):
            self.recalculate_course(options['course'])
        elif options.get('enrollment'):
            self.recalculate_enrollment(options['enrollment'])
        elif options.get('all'):
            self.recalculate_all()
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Please specify --user, --course, --enrollment, or --all'
                )
            )

    def recalculate_user(self, user_id):
        """Recalculate progress for a single user"""
        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(f'Recalculating progress for user: {user.email}')
            recalculate_all_user_progress(user)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully recalculated progress for {user.email}'
                )
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with ID {user_id} not found')
            )

    def recalculate_course(self, course_id):
        """Recalculate progress for all users in a course"""
        try:
            course = Course.objects.get(id=course_id)
            self.stdout.write(
                f'Recalculating progress for all users in course: {course.code}'
            )
            
            enrollments = CourseEnrollment.objects.filter(course=course)
            count = enrollments.count()
            
            for idx, enrollment in enumerate(enrollments, 1):
                recalculate_course_enrollment_progress(enrollment)
                if idx % 10 == 0:
                    self.stdout.write(f'  Processed {idx}/{count} enrollments...')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully recalculated progress for {count} enrollments '
                    f'in course {course.code}'
                )
            )
        except Course.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Course with ID {course_id} not found')
            )

    def recalculate_enrollment(self, enrollment_id):
        """Recalculate progress for a specific enrollment"""
        try:
            enrollment = CourseEnrollment.objects.get(id=enrollment_id)
            self.stdout.write(
                f'Recalculating progress for enrollment: '
                f'{enrollment.user.email} - {enrollment.course.code}'
            )
            recalculate_course_enrollment_progress(enrollment)
            self.stdout.write(
                self.style.SUCCESS('Successfully recalculated enrollment progress')
            )
        except CourseEnrollment.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Enrollment with ID {enrollment_id} not found')
            )

    def recalculate_all(self):
        """Recalculate progress for all users"""
        users = User.objects.all()
        count = users.count()
        
        self.stdout.write(f'Recalculating progress for all {count} users...')
        
        for idx, user in enumerate(users, 1):
            recalculate_all_user_progress(user)
            if idx % 50 == 0:
                self.stdout.write(f'  Processed {idx}/{count} users...')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully recalculated progress for {count} users'
            )
        )
