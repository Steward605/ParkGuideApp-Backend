from django.core.management.base import BaseCommand
from courses.models import Course, Chapter, Lesson, PracticeExercise, Quiz
import sys


class Command(BaseCommand):
    help = 'Load sample course data with full logging to file'

    def handle(self, *args, **options):
        logfile = '/tmp/load_courses.log'
        
        with open(logfile, 'w') as log:
            log.write("=== LOAD SAMPLE DATA ===\n\n")
            
            # Clear old data
            log.write("**STEP 1: Clearing old data**\n")
            Course.objects.all().delete()
            log.write(f"  Courses remaining: {Course.objects.count()}\n\n")
            
            # Create courses
            log.write("**STEP 2: Creating courses**\n")
            course_data = [
                {
                    'code': 'park-guide-101',
                    'title_en': 'Park Guide Fundamentals',
                    'chapters': [
                        {
                            'title_en': 'Park Orientation & Safety',
                            'lessons': 2,
                        },
                        {
                            'title_en': 'Wildlife & Ecology',
                            'lessons': 1,
                        },
                    ]
                },
                {
                    'code': 'park-guide-201',
                    'title_en': 'Advanced Guiding Techniques',
                    'chapters': [
                        {
                            'title_en': 'Interpretation Skills',
                            'lessons': 1,
                        },
                    ]
                },
            ]
            
            for idx, course_spec in enumerate(course_data):
                course = Course.objects.create(
                    code=course_spec['code'],
                    title={'en': course_spec['title_en'], 'ms': '', 'zh': ''},
                    is_published=True
                )
                log.write(f"  {idx+1}. Created Course ID {course.id}: {course.code}\n")
                
                # Create chapters
                for ch_idx, chapter_spec in enumerate(course_spec['chapters']):
                    chapter = Chapter.objects.create(
                        course=course,
                        title={'en': chapter_spec['title_en'], 'ms': '', 'zh': ''},
                        order=ch_idx + 1
                    )
                    log.write(f"     Created Chapter ID {chapter.id}: {chapter.title['en']}\n")
                    
                    # Create lessons
                    for lesson_idx in range(chapter_spec['lessons']):
                        lesson = Lesson.objects.create(
                            chapter=chapter,
                            title={'en': f'Lesson {lesson_idx+1}', 'ms': '', 'zh': ''},
                            order=lesson_idx + 1
                        )
                        log.write(f"       Created Lesson ID {lesson.id}\n")
            
            # Verify
            log.write("\n**STEP 3: Verification**\n")
            c_count = Course.objects.count()
            ch_count = Chapter.objects.count()
            l_count = Lesson.objects.count()
            
            log.write(f"  Total Courses: {c_count}\n")
            log.write(f"  Total Chapters: {ch_count}\n")
            log.write(f"  Total Lessons: {l_count}\n\n")
            
            # List all
            log.write("**STEP 4: Course Structure**\n")
            for course in Course.objects.all():
                log.write(f"Course {course.id}: {course.code} ({course.chapters.count()} chapters)\n")
                for chapter in course.chapters.all():
                    log.write(f"  - Chapter {chapter.id}: {chapter.title['en']} ({chapter.lessons.count()} lessons)\n")
            
            log.write("\n✓ COMPLETED\n")
        
        # Print path to log file
        self.stdout.write(self.style.SUCCESS(f"✓ Data loaded. Log: {logfile}"))
        
        # Also print to console
        with open(logfile, 'r') as f:
            print(f.read())
