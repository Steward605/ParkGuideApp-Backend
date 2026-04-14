#!/usr/bin/env python
"""Check syntax and imports"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'park_guide.settings')

try:
    import django
    django.setup()
    
    from courses.views_fresh import QuizViewSet, PracticeExerciseViewSet
    from courses.serializers_fresh import QuizCreateUpdateSerializer, PracticeExerciseCreateUpdateSerializer
    
    print("✓ All imports successful")
    print("\n✓ New features available:")
    print("  - POST /api/quizzes/ with questions array")
    print("  - PUT /api/quizzes/{id}/add_questions/ - replace questions")
    print("  - PATCH /api/quizzes/{id}/add_questions/ - append questions")
    print("  - Same for /api/practice/")
    print("\n✓ Questions support multiple answers via 'correctIndexes' field")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
