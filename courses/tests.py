from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import CustomUser
from .models import Course, Module, Chapter, Quiz
from .models import CourseProgress, ModuleProgress
from .serializers import ModuleSerializer
from courses.models import CourseEnrollment


class ModuleSerializerQuizSupportTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(title={'en': 'Test Course'})

    def test_legacy_single_quiz_representation(self):
        module = Module.objects.create(
            course=self.course,
            title={'en': 'Module 1'},
            quiz={
                'question': {'en': 'Q1'},
                'options': {'en': ['A', 'B']},
                'correctIndex': 0,
            },
        )

        payload = ModuleSerializer(module).data

        self.assertEqual(payload['quiz']['question']['en'], 'Q1')
        self.assertEqual(len(payload['quizzes']), 1)
        self.assertEqual(payload['quizzes'][0]['question']['en'], 'Q1')

    def test_update_module_with_multiple_quizzes(self):
        module = Module.objects.create(
            course=self.course,
            title={'en': 'Module 2'},
            content={'en': 'Body'},
            quiz=[],
        )

        serializer = ModuleSerializer(module, data={
            'quizzes': [
                {
                    'question': {'en': 'Q1'},
                    'options': {'en': ['A', 'B']},
                    'correctIndex': 0,
                },
                {
                    'question': {'en': 'Q2'},
                    'options': {'en': ['C', 'D']},
                    'correctIndex': 1,
                },
            ],
        }, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        module = serializer.save()

        self.assertEqual(len(module.quiz), 2)
        self.assertEqual(module.quiz[1]['question']['en'], 'Q2')

    def test_multi_answer_question_with_two_correct_indexes(self):
        module = Module.objects.create(
            course=self.course,
            title={'en': 'Module 3'},
            content={'en': 'Body'},
            quiz=[],
        )

        serializer = ModuleSerializer(module, data={
            'quizzes': [
                {
                    'question': {'en': 'Choose two'},
                    'options': {'en': ['A', 'B', 'C']},
                    'correctIndexes': [0, 2],
                }
            ],
        }, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.quiz[0]['correctIndexes'], [0, 2])
        self.assertNotIn('correctIndex', updated.quiz[0])

    def test_multi_answer_question_rejects_more_than_three_answers(self):
        module = Module.objects.create(
            course=self.course,
            title={'en': 'Module 4'},
            content={'en': 'Body'},
            quiz=[],
        )

        serializer = ModuleSerializer(module, data={
            'quizzes': [
                {
                    'question': {'en': 'Choose too many'},
                    'options': {'en': ['A', 'B', 'C', 'D']},
                    'correctIndexes': [0, 1, 2, 3],
                }
            ],
        }, partial=True)

        self.assertFalse(serializer.is_valid())


class ProgressUpsertTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='tester@example.com',
            username='tester',
            password='password123',
        )
        self.client.force_authenticate(user=self.user)

        self.course = Course.objects.create(title={'en': 'Course'})
        self.module = Module.objects.create(course=self.course, title={'en': 'Module'})

    def test_module_progress_create_then_amend_keeps_same_id(self):
        url = reverse('progress-list')

        first = self.client.post(url, {'module': self.module.id, 'completed': False}, format='json')
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        first_id = first.data['id']

        second = self.client.post(url, {'module': self.module.id, 'completed': True}, format='json')
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(second.data['id'], first_id)

        progress = ModuleProgress.objects.get(user=self.user, module=self.module)
        self.assertTrue(progress.completed)

    def test_course_progress_create_then_amend_keeps_same_id(self):
        url = reverse('course-progress-list')

        first = self.client.post(
            url,
            {
                'course': self.course.id,
                'completed_modules': 1,
                'total_modules': 3,
                'progress': 0.33,
                'completed': False,
            },
            format='json',
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        first_id = first.data['id']

        second = self.client.post(
            url,
            {
                'course': self.course.id,
                'completed_modules': 2,
                'total_modules': 3,
                'progress': 0.66,
                'completed': False,
            },
            format='json',
        )
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(second.data['id'], first_id)

        progress = CourseProgress.objects.get(user=self.user, course=self.course)
        self.assertEqual(progress.completed_modules, 2)
        self.assertEqual(progress.total_modules, 3)


class FreshEnrollmentApiTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='learner@example.com',
            username='learner',
            password='password123',
        )
        self.client.force_authenticate(user=self.user)

        self.prereq = Course.objects.create(
            code='PRE101',
            title={'en': 'Prerequisite'},
            description={'en': 'Prereq course'},
            is_published=True,
        )
        self.course = Course.objects.create(
            code='ADV201',
            title={'en': 'Advanced Course'},
            description={'en': 'Advanced content'},
            is_published=True,
        )
        self.course.prerequisites.add(self.prereq)

    def test_course_detail_exposes_enrollment_metadata(self):
        response = self.client.get(f'/api/courses/{self.course.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('enrollment_status', response.data)
        self.assertEqual(response.data['enrollment_status'], None)
        self.assertEqual(response.data['prerequisites_info'][0]['code'], 'PRE101')
        self.assertFalse(response.data['prerequisites_info'][0]['is_completed'])

    def test_enroll_rejects_missing_prerequisite(self):
        response = self.client.post(f'/api/courses/{self.course.id}/enroll/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('course', response.data)
        self.assertEqual(CourseEnrollment.objects.count(), 0)

    def test_enroll_and_status_and_enrollment_list(self):
        CourseEnrollment.objects.create(
            user=self.user,
            course=self.prereq,
            status='completed',
        )

        enroll_response = self.client.post(f'/api/courses/{self.course.id}/enroll/', {}, format='json')
        self.assertEqual(enroll_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(enroll_response.data['course'], self.course.id)
        self.assertEqual(enroll_response.data['status'], 'enrolled')

        status_response = self.client.get(f'/api/courses/{self.course.id}/enrollment_status/')
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)
        self.assertEqual(status_response.data['course'], self.course.id)

        list_response = self.client.get('/api/enrollments/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 2)

    def test_enroll_uses_json_prerequisites_when_db_relation_missing(self):
        self.course.prerequisites.clear()

        response = self.client.post(f'/api/courses/{self.course.id}/enroll/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('PRE101', response.data['course'][0])


class FreshQuizSubmissionTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='quizzer@example.com',
            username='quizzer',
            password='password123',
        )
        self.client.force_authenticate(user=self.user)

        self.course = Course.objects.create(
            code='QUIZ101',
            title={'en': 'Quiz Course'},
            description={'en': 'Quiz course'},
            is_published=True,
        )
        self.chapter = Chapter.objects.create(
            course=self.course,
            title={'en': 'Chapter 1'},
            description={'en': 'Intro'},
            order=1,
        )
        self.quiz = Quiz.objects.create(
            chapter=self.chapter,
            title={'en': 'Quiz 1'},
            description={'en': 'Test quiz'},
            questions=[
                {
                    'question': {'en': '2 + 2 = ?'},
                    'options': {'en': ['3', '4', '5']},
                    'correctIndex': 1,
                    'explanation': 'Basic math',
                }
            ],
            passing_score=70,
            order=1,
        )

    def test_repeated_quiz_submission_increments_attempt_number(self):
        payload = {'answers': {'0': 1}, 'time_spent': 12}

        first = self.client.post(f'/api/quizzes/{self.quiz.id}/submit/', payload, format='json')
        second = self.client.post(f'/api/quizzes/{self.quiz.id}/submit/', payload, format='json')

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first.data['attempt_number'], 1)
        self.assertEqual(second.data['attempt_number'], 2)

    def test_quiz_submission_accepts_array_answers(self):
        response = self.client.post(
            f'/api/quizzes/{self.quiz.id}/submit/',
            {'answers': [1], 'time_spent': 5},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['score'], 100.0)
        self.assertTrue(response.data['passed'])

    def test_quiz_submission_accepts_is_correct_option_format(self):
        self.quiz.questions = [
            {
                'question_text': {'en': 'Which answer is correct?'},
                'options': [
                    {'text': {'en': 'Wrong'}, 'is_correct': False},
                    {'text': {'en': 'Right'}, 'is_correct': True},
                ],
            }
        ]
        self.quiz.save(update_fields=['questions'])

        response = self.client.post(
            f'/api/quizzes/{self.quiz.id}/submit/',
            {'answers': [1], 'time_spent': 5},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['score'], 100.0)
        self.assertTrue(response.data['passed'])

    def test_quiz_submission_updates_course_progress(self):
        course_response = self.client.post(f'/api/courses/{self.course.id}/enroll/', {}, format='json')
        self.assertIn(course_response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

        lesson = self.chapter.lessons.create(
            title={'en': 'Lesson 1'},
            content_text={'en': 'Body'},
            order=1,
            estimated_time=5,
        )
        self.client.post(f'/api/lessons/{lesson.id}/mark_complete/', {}, format='json')

        response = self.client.post(
            f'/api/quizzes/{self.quiz.id}/submit/',
            {'answers': [1], 'time_spent': 5},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        enrollment = CourseEnrollment.objects.get(user=self.user, course=self.course)
        self.assertGreater(enrollment.progress_percentage, 0)


class FreshCourseCatalogCompatibilityTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='catalog@example.com',
            username='catalog',
            password='password123',
        )
        self.client.force_authenticate(user=self.user)
        self.course = Course.objects.create(
            code='park-guide-101',
            title={'en': 'Park Guide 101'},
            description={'en': 'Intro course'},
            thumbnail='https://images.unsplash.com/photo-1488749807830-63789f68bb65?w=400',
            is_published=True,
        )

    def test_course_list_uses_safe_thumbnail_fallback(self):
        response = self.client.get('/api/courses/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data[0]['thumbnail'].endswith('/static/images/icon.png'))
