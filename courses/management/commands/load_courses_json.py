import json
import os
from django.core.management.base import BaseCommand
from courses.models import Course, Chapter, Lesson, PracticeExercise, Quiz


class Command(BaseCommand):
    help = 'Load complete course data from JSON file'

    def handle(self, *args, **options):
        # Get the JSON file path
        json_file = os.path.join(
            os.path.dirname(__file__),
            '../../data/courses_complete.json'
        )

        self.stdout.write(self.style.WARNING(f'Loading data from: {json_file}'))

        # Check if file exists
        if not os.path.exists(json_file):
            self.stdout.write(self.style.ERROR(f'❌ File not found: {json_file}'))
            return

        # Load JSON data
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                courses_data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'❌ JSON parsing error: {e}'))
            return

        # Clear existing data
        self.stdout.write(self.style.WARNING('Clearing existing courses...'))
        Course.objects.all().delete()

        # Load courses
        self.stdout.write(self.style.SUCCESS('🚀 Starting data load...\n'))

        for course_data in courses_data:
            self.stdout.write(f'📚 Creating course: {course_data["title"]["en"]}')

            # Create course
            course = Course.objects.create(
                code=course_data['code'],
                title=course_data['title'],
                description=course_data.get('description', {}),
                thumbnail=course_data.get('thumbnail', ''),
                is_published=course_data.get('is_published', True)
            )
            self.stdout.write(f'   ✓ Course created (ID: {course.id})')

            # Create chapters
            for chapter_index, chapter_data in enumerate(course_data.get('chapters', [])):
                self.stdout.write(f'   📖 Chapter {chapter_index + 1}: {chapter_data["title"]["en"]}')

                chapter = Chapter.objects.create(
                    course=course,
                    title=chapter_data['title'],
                    description=chapter_data.get('description', {}),
                    order=chapter_index + 1
                )

                # Create lessons
                for lesson_index, lesson_data in enumerate(chapter_data.get('lessons', [])):
                    self.stdout.write(f'      📝 Lesson {lesson_index + 1}: {lesson_data["title"]["en"]}')

                    Lesson.objects.create(
                        chapter=chapter,
                        title=lesson_data['title'],
                        content_text=lesson_data.get('content_text', {}),
                        content_images=lesson_data.get('content_images', []),
                        content_videos=lesson_data.get('content_videos', []),
                        order=lesson_index + 1,
                        estimated_time=lesson_data.get('estimated_time', 10)
                    )

                # Create practice exercises
                for exercise_index, exercise_data in enumerate(chapter_data.get('exercises', [])):
                    self.stdout.write(f'      🎯 Exercise {exercise_index + 1}: {exercise_data["title"]["en"]}')

                    PracticeExercise.objects.create(
                        chapter=chapter,
                        title=exercise_data['title'],
                        exercise_type=exercise_data.get('exercise_type', 'multiple_choice'),
                        questions=exercise_data.get('questions', []),
                        order=exercise_index + 1
                    )

                # Create quizzes
                for quiz_index, quiz_data in enumerate(chapter_data.get('quizzes', [])):
                    self.stdout.write(f'      ✅ Quiz {quiz_index + 1}: {quiz_data["title"]["en"]}')

                    Quiz.objects.create(
                        chapter=chapter,
                        title=quiz_data['title'],
                        time_limit=quiz_data.get('time_limit', 30),
                        questions=quiz_data.get('questions', []),
                        order=quiz_index + 1
                    )

            self.stdout.write('')

        # SECOND PASS: Load prerequisites (must be done after all courses exist)
        self.stdout.write(self.style.WARNING('\n🔗 Loading prerequisites relationships...\n'))
        
        for course_data in courses_data:
            course = Course.objects.get(code=course_data['code'])
            prerequisites = course_data.get('prerequisites', [])
            
            if prerequisites:
                prerequisite_codes = []
                for prereq_code in prerequisites:
                    try:
                        prereq_course = Course.objects.get(code=prereq_code)
                        course.prerequisites.add(prereq_course)
                        prerequisite_codes.append(prereq_code)
                        self.stdout.write(f'  ✓ {course.code} → requires {prereq_code}')
                    except Course.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'  ❌ Prerequisite course not found: {prereq_code}'))
            else:
                self.stdout.write(f'  • {course.code} - No prerequisites')

        # Verify and display summary
        course_count = Course.objects.count()
        chapter_count = Chapter.objects.count()
        lesson_count = Lesson.objects.count()
        exercise_count = PracticeExercise.objects.count()
        quiz_count = Quiz.objects.count()

        self.stdout.write(self.style.SUCCESS('\n✅ Data load completed successfully!\n'))
        self.stdout.write(self.style.SUCCESS('📊 Summary:'))
        self.stdout.write(f'   📚 Courses: {course_count}')
        self.stdout.write(f'   📖 Chapters: {chapter_count}')
        self.stdout.write(f'   📝 Lessons: {lesson_count}')
        self.stdout.write(f'   🎯 Practice Exercises: {exercise_count}')
        self.stdout.write(f'   ✅ Quizzes: {quiz_count}')
        
        # Show prerequisite chain
        self.stdout.write(self.style.SUCCESS('\n📚 Course Prerequisite Chain:'))
        for course in Course.objects.all().order_by('code'):
            prereqs = course.prerequisites.all()
            if prereqs:
                prereq_str = ' → '.join([p.code for p in prereqs])
                self.stdout.write(f'   {course.code} ← {prereq_str}')
            else:
                self.stdout.write(f'   {course.code} (Entry Level)')
        
        self.stdout.write('')
