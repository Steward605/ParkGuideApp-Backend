"""
Fresh course loading system - Complete rewrite
Loads courses from courses_complete.json with full structure
"""
import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from courses.models import Course, Chapter, Lesson, PracticeExercise, Quiz


class Command(BaseCommand):
    help = 'Load courses from JSON data file (complete rewrite)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing courses before loading'
        )
        parser.add_argument(
            '--file',
            type=str,
            default='courses_complete.json',
            help='JSON file to load from'
        )

    def handle(self, *args, **options):
        # Clear existing if requested
        if options['clear']:
            self.stdout.write("Clearing existing courses...")
            Course.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✓ Cleared"))

        # Find JSON file
        json_path = os.path.join('courses', 'data', options['file'])
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f'File not found: {json_path}'))
            return

        # Load JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            courses_data = json.load(f)

        if not isinstance(courses_data, list):
            courses_data = [courses_data]

        # Load courses with transaction
        loaded_count = 0
        try:
            with transaction.atomic():
                loaded_courses = []
                for course_data in courses_data:
                    course = self._create_course(course_data)
                    if course:
                        loaded_courses.append((course, course_data))
                        loaded_count += 1

                self._sync_prerequisites(loaded_courses)

            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Successfully loaded {loaded_count} courses!')
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error loading courses: {str(e)}'))
            raise

    def _create_course(self, data):
        """Create course with all nested content"""
        self.stdout.write(f"Loading: {data.get('code', 'unknown')}...", ending=' ')

        try:
            # Get or create course
            course, created = Course.objects.get_or_create(
                code=data['code'],
                defaults={
                    'title': data.get('title', {}),
                    'description': data.get('description', {}),
                    'thumbnail': data.get('thumbnail', ''),
                    'is_published': data.get('is_published', True),
                }
            )

            if not created:
                # Update existing course
                course.title = data.get('title', course.title)
                course.description = data.get('description', course.description)
                course.thumbnail = data.get('thumbnail', course.thumbnail)
                course.is_published = data.get('is_published', course.is_published)
                course.save()

            # Load chapters
            chapters_data = data.get('chapters', [])
            for ch_idx, chapter_data in enumerate(chapters_data):
                self._create_chapter(course, chapter_data, ch_idx + 1)

            self.stdout.write(self.style.SUCCESS(f"✓ {course.code}"))
            return course

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error: {str(e)}"))
            raise

    def _sync_prerequisites(self, loaded_courses):
        """Sync prerequisite relationships after all courses exist."""
        self.stdout.write("\nSyncing prerequisites...", ending=' ')

        for course, course_data in loaded_courses:
            prerequisite_codes = course_data.get('prerequisites', [])
            prerequisite_courses = Course.objects.filter(code__in=prerequisite_codes)
            course.prerequisites.set(prerequisite_courses)

        self.stdout.write(self.style.SUCCESS("✓"))

    def _create_chapter(self, course, data, order):
        """Create chapter with all nested content"""
        chapter, _ = Chapter.objects.get_or_create(
            course=course,
            order=order,
            defaults={
                'title': data.get('title', {}),
                'description': data.get('description', {}),
            }
        )

        # Load lessons
        lessons_data = data.get('lessons', [])
        for les_idx, lesson_data in enumerate(lessons_data):
            self._create_lesson(chapter, lesson_data, les_idx + 1)

        # Load practice exercises
        exercises_data = data.get('exercises', [])
        for ex_idx, exercise_data in enumerate(exercises_data):
            self._create_exercise(chapter, exercise_data, les_idx + ex_idx + 2)

        # Load quizzes
        quizzes_data = data.get('quizzes', [])
        for q_idx, quiz_data in enumerate(quizzes_data):
            self._create_quiz(chapter, quiz_data, len(lessons_data) + len(exercises_data) + q_idx + 1)

        return chapter

    def _create_lesson(self, chapter, data, order):
        """Create lesson"""
        lesson, _ = Lesson.objects.get_or_create(
            chapter=chapter,
            order=order,
            defaults={
                'title': data.get('title', {}),
                'content_text': data.get('content_text', {}),
                'content_images': data.get('content_images', []),
                'content_videos': data.get('content_videos', []),
                'estimated_time': data.get('estimated_time', 10),
            }
        )
        return lesson

    def _create_exercise(self, chapter, data, order):
        """Create practice exercise"""
        exercise, _ = PracticeExercise.objects.get_or_create(
            chapter=chapter,
            order=order,
            defaults={
                'title': data.get('title', {}),
                'description': data.get('description', {}),
                'exercise_type': data.get('type', 'multiple_choice'),
                'questions': data.get('questions', []),
                'passing_score': data.get('passing_score', 70),
            }
        )
        return exercise

    def _create_quiz(self, chapter, data, order):
        """Create quiz"""
        quiz, _ = Quiz.objects.get_or_create(
            chapter=chapter,
            order=order,
            defaults={
                'title': data.get('title', {}),
                'description': data.get('description', {}),
                'questions': data.get('questions', []),
                'passing_score': data.get('passing_score', 70),
                'time_limit': data.get('time_limit', 30),
                'show_answers': data.get('show_answers', True),
            }
        )
        return quiz
