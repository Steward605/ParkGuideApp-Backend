import json
from django.core.management.base import BaseCommand
from django.db import transaction
from courses.models import (
    Course, Chapter, Lesson, PracticeExercise, Quiz,
    CourseEnrollment
)

class Command(BaseCommand):
    help = 'Load comprehensive stress test course data'

    def handle(self, *args, **options):
        # Load course data
        with open('courses/data/courses_stress_test.json', 'r', encoding='utf-8') as f:
            courses_data = json.load(f)
        
        self.stdout.write(f"Loading {len(courses_data)} courses...")
        
        with transaction.atomic():
            for course_data in courses_data:
                # Create or update course
                course, created = Course.objects.update_or_create(
                    code=course_data['code'],
                    defaults={
                        'title': course_data['title'],
                        'description': course_data['description'],
                        'thumbnail': course_data['thumbnail'],
                        'is_published': course_data['is_published'],
                    }
                )
                
                status = "✓ Created" if created else "⟳ Updated"
                self.stdout.write(f"  {status}: {course.code}")
                
                # Add prerequisites
                prereq_codes = course_data.get('prerequisites', [])
                for prereq_code in prereq_codes:
                    try:
                        prereq_course = Course.objects.get(code=prereq_code)
                        course.prerequisites.add(prereq_course)
                    except Course.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f"    ⚠ Prerequisite {prereq_code} not found")
                        )
                
                # Create chapters
                for chapter_idx, chapter_data in enumerate(course_data.get('chapters', [])):
                    chapter, _ = Chapter.objects.update_or_create(
                        course=course,
                        order=chapter_idx,
                        defaults={
                            'title': chapter_data['title'],
                            'description': chapter_data.get('description', {}),
                        }
                    )
                    
                    # Create lessons
                    for lesson_idx, lesson_data in enumerate(chapter_data.get('lessons', [])):
                        Lesson.objects.update_or_create(
                            chapter=chapter,
                            order=lesson_idx,
                            defaults={
                                'title': lesson_data['title'],
                                'content_text': lesson_data.get('content_text', {}),
                                'content_images': lesson_data.get('content_images', []),
                                'content_videos': lesson_data.get('content_videos', []),
                                'estimated_time': lesson_data.get('estimated_time', 15),
                            }
                        )
                    
                    # Create practice exercises
                    for exercise_idx, exercise_data in enumerate(chapter_data.get('exercises', [])):
                        PracticeExercise.objects.update_or_create(
                            chapter=chapter,
                            order=100 + exercise_idx,
                            defaults={
                                'title': exercise_data['title'],
                                'description': exercise_data.get('description', {}),
                                'questions': exercise_data.get('questions', []),
                                'passing_score': exercise_data.get('passing_score', 70),
                                'exercise_type': 'mixed',
                            }
                        )
                    
                    # Create quizzes
                    for quiz_idx, quiz_data in enumerate(chapter_data.get('quizzes', [])):
                        Quiz.objects.update_or_create(
                            chapter=chapter,
                            order=quiz_idx,
                            defaults={
                                'title': quiz_data['title'],
                                'description': quiz_data.get('description', {}),
                                'questions': quiz_data.get('questions', []),
                                'passing_score': quiz_data.get('passing_score', 70),
                                'time_limit': quiz_data.get('time_limit'),
                            }
                        )
                    
                    self.stdout.write(
                        f"    ✓ Chapter: {chapter.title.get('en', 'Untitled')} "
                        f"({len(chapter_data.get('lessons', []))} lessons, "
                        f"{len(chapter_data.get('quizzes', []))} quizzes)"
                    )
        
        self.stdout.write(self.style.SUCCESS('✓ Comprehensive course data loaded successfully!'))
