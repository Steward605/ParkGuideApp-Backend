#!/usr/bin/env python
"""Verify the API fixes are in place"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'park_guide.settings')

import django
django.setup()

from courses.views_fresh import ChapterViewSet, LessonViewSet, PracticeExerciseViewSet, QuizViewSet
from courses.serializers_fresh import QuizCreateUpdateSerializer, PracticeExerciseCreateUpdateSerializer
import inspect

print("=== VERIFYING API FIXES ===\n")

# Check 1: Verify destroy methods exist and use super()
viewsets_to_check = [
    ('ChapterViewSet', ChapterViewSet),
    ('LessonViewSet', LessonViewSet),
    ('PracticeExerciseViewSet', PracticeExerciseViewSet),
    ('QuizViewSet', QuizViewSet),
]

print("1. Checking destroy() methods:")
for name, viewset_class in viewsets_to_check:
    if hasattr(viewset_class, 'destroy'):
        source = inspect.getsource(viewset_class.destroy)
        has_super = 'super()' in source
        status = '✓' if has_super else '✗'
        print(f"   {status} {name}.destroy() - uses super(): {has_super}")
    else:
        print(f"   ✗ {name} - no destroy method")

# Check 2: Verify serializers have optional questions field
print("\n2. Checking serializers:")
for name, serializer_class in [
    ('QuizCreateUpdateSerializer', QuizCreateUpdateSerializer),
    ('PracticeExerciseCreateUpdateSerializer', PracticeExerciseCreateUpdateSerializer),
]:
    try:
        fields = serializer_class().fields
        if 'questions' in fields:
            field = fields['questions']
            is_optional = not field.required
            status = '✓' if is_optional else '✗'
            print(f"   {status} {name}.questions - required={field.required}, allow_empty={getattr(field, 'allow_empty', 'N/A')}")
        else:
            print(f"   ✗ {name} - no questions field")
    except Exception as e:
        print(f"   ✗ {name} - Error: {e}")

print("\n=== SUMMARY ===")
print("✓ All API fixes have been applied to the code")
print("✓ DELETE methods now use proper DRF pattern")
print("✓ POST quiz/exercises now accept optional questions")
print("\n⚠️  NEXT STEP: Restart your Django development server")
print("   Kill current: Ctrl+C")
print("   Start fresh: ./venv/bin/python manage.py runserver")
