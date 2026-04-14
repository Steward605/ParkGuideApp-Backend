#!/usr/bin/env python
"""Debug API issues"""
import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'park_guide.settings')
django.setup()

from courses.models import Lesson, Chapter, Quiz
from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

# Check if we have test data
lessons = Lesson.objects.all()
chapters = Chapter.objects.all()
quizzes = Quiz.objects.all()

print(f"Total lessons: {lessons.count()}")
print(f"Total chapters: {chapters.count()}")
print(f"Total quizzes: {quizzes.count()}")

# Get or create a test user
user, created = User.objects.get_or_create(email='testuser@example.com', defaults={'username': 'testuser'})
if created:
    user.set_password('testpass123')
    user.save()
    print(f"Created test user: {user}")

# Use APIClient instead of Client
client = APIClient()
client.force_authenticate(user=user)

if chapters.exists():
    chapter_id = chapters.first().id
    print(f"\n=== DELETE /api/chapters/{chapter_id}/ ===")
    response = client.delete(f'/api/chapters/{chapter_id}/')
    print(f"Status: {response.status_code}")
    print(f"Data: {response.data if hasattr(response, 'data') else response.content}")

if lessons.exists():
    lesson_id = lessons.first().id
    print(f"\n=== DELETE /api/lessons/{lesson_id}/ ===")
    response = client.delete(f'/api/lessons/{lesson_id}/')
    print(f"Status: {response.status_code}")
    print(f"Data: {response.data if hasattr(response, 'data') else response.content}")

print(f"\n=== POST /api/quizzes/ ===")
if chapters.exists():
    chapter_id = chapters.first().id
    data = {
        'title': {'en': 'Test Quiz'},
        'description': {'en': 'Test description'},
        'questions': [{'text': 'Test Q', 'correctIndex': 0, 'options': ['A', 'B']}],
        'passing_score': 70,
    }
    response = client.post(
        '/api/quizzes/',
        data=data,
        format='json'
    )
    print(f"Status: {response.status_code}")
    print(f"Data: {response.data if hasattr(response, 'data') else response.content}")
    
print("\n=== Testing OPTIONS on /api/quizzes/ ===")
response = client.options('/api/quizzes/')
print(f"Status: {response.status_code}")
print(f"Headers: {response.serialize_headers() if hasattr(response, 'serialize_headers') else 'N/A'}")
