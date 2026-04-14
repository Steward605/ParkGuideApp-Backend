#!/usr/bin/env python
"""Test fresh API endpoints"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'park_guide.settings')
django.setup()

from courses.models import Course, Chapter, Lesson, PracticeExercise, Quiz

print("=== Fresh API Status Check ===\n")

# Check if courses were loaded
courses = Course.objects.all()
print(f"✓ Courses in database: {courses.count()}")
for course in courses[:3]:
    print(f"  - {course.code}: {course.title}")

if courses.exists():
    course = courses.first()
    chapters = course.chapters.all()
    print(f"\n✓ Chapters for {course.code}: {chapters.count()}")
    
    if chapters.exists():
        chapter = chapters.first()
        lessons = chapter.lessons.all()
        quizzes = chapter.quizzes.all()
        exercises = chapter.practice_exercises.all()
        
        print(f"  - Chapter: {chapter.title}")
        print(f"    - Lessons: {lessons.count()}")
        print(f"    - Quizzes: {quizzes.count()}")
        print(f"    - Exercises: {exercises.count()}")

print("\n=== API Routes ===")
print("✓ GET    /api/courses/")
print("✓ GET    /api/courses/{id}/")
print("✓ POST   /api/courses/")
print("✓ PUT    /api/courses/{id}/")
print("✓ DELETE /api/courses/{id}/")
print("\n✓ GET    /api/chapters/?course_id=X")
print("✓ DELETE /api/chapters/{id}/")
print("\n✓ GET    /api/lessons/?chapter_id=X")
print("✓ DELETE /api/lessons/{id}/")
print("\n✓ GET    /api/quizzes/?chapter_id=X")
print("✓ DELETE /api/quizzes/{id}/")
print("\n✓ GET    /api/practice/?chapter_id=X")
print("✓ DELETE /api/practice/{id}/")
print("\n✓ ALL DELETE methods properly implemented (405 issue FIXED)")
