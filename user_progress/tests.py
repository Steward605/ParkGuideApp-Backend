from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import CustomUser
from courses.models import Chapter, ChapterProgress, Course, CourseEnrollment, Module, ModuleProgress
from notifications.models import UserNotification

from .management.commands.seed_demo_badges import Command as SeedBadgeCommand
from .models import Badge, UserBadge
from .services import (
    auto_approve_pending_badges,
    auto_reject_pending_badges,
    ensure_badge_rows_for_user,
    revoke_badge_from_ineligible_users,
    sync_user_badges,
)


class BadgeServiceTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='password123',
            is_staff=True,
        )
        self.user1 = CustomUser.objects.create_user(
            email='user1@example.com',
            username='user1',
            password='password123',
        )
        self.user2 = CustomUser.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='password123',
        )

        self.course = Course.objects.create(title={'en': 'Badge Course'})
        self.module1 = Module.objects.create(course=self.course, title={'en': 'M1'})
        self.module2 = Module.objects.create(course=self.course, title={'en': 'M2'})
        self.module3 = Module.objects.create(course=self.course, title={'en': 'M3'})

        self.badge = Badge.objects.create(
            name='Explorer',
            required_completed_modules=2,
            is_active=True,
        )

    def test_new_users_receive_in_progress_badge_rows(self):
        ensure_badge_rows_for_user(self.user1)
        user_badge = UserBadge.objects.get(user=self.user1, badge=self.badge)
        self.assertEqual(user_badge.status, UserBadge.STATUS_IN_PROGRESS)
        self.assertFalse(user_badge.is_awarded)

    def test_sync_user_badges_moves_eligible_user_to_pending(self):
        ModuleProgress.objects.create(user=self.user1, module=self.module1, completed=True)
        ModuleProgress.objects.create(user=self.user1, module=self.module2, completed=True)

        sync_user_badges(self.user1, admin_user=self.admin)

        user_badge = UserBadge.objects.get(user=self.user1, badge=self.badge)
        self.assertEqual(user_badge.status, UserBadge.STATUS_PENDING)
        self.assertFalse(user_badge.is_awarded)

        admin_notification = UserNotification.objects.filter(
            user=self.admin,
            notification__title__icontains='Badge approval needed',
        ).first()
        self.assertIsNotNone(admin_notification)

    def test_module_progress_signal_moves_eligible_user_to_pending(self):
        ModuleProgress.objects.create(user=self.user1, module=self.module1, completed=True)
        ModuleProgress.objects.create(user=self.user1, module=self.module2, completed=True)

        user_badge = UserBadge.objects.get(user=self.user1, badge=self.badge)
        self.assertEqual(user_badge.status, UserBadge.STATUS_PENDING)
        self.assertFalse(user_badge.is_awarded)

    def test_revoke_badge_when_user_becomes_ineligible_moves_back_to_in_progress(self):
        ModuleProgress.objects.create(user=self.user1, module=self.module1, completed=True)
        ModuleProgress.objects.create(user=self.user1, module=self.module2, completed=True)
        sync_user_badges(self.user1, admin_user=self.admin)
        auto_approve_pending_badges(self.badge, admin_user=self.admin)

        progress_row = ModuleProgress.objects.get(user=self.user1, module=self.module2)
        progress_row.completed = False
        progress_row.save(update_fields=['completed'])

        revoked = revoke_badge_from_ineligible_users(self.badge, admin_user=self.admin)

        user_badge = UserBadge.objects.get(user=self.user1, badge=self.badge)
        self.assertIn(revoked, (0, 1))
        self.assertEqual(user_badge.status, UserBadge.STATUS_IN_PROGRESS)
        self.assertFalse(user_badge.is_awarded)

    def test_auto_reject_pending_badges(self):
        ModuleProgress.objects.create(user=self.user1, module=self.module1, completed=True)
        ModuleProgress.objects.create(user=self.user1, module=self.module2, completed=True)
        sync_user_badges(self.user1, admin_user=self.admin)
        rejected = auto_reject_pending_badges(self.badge, admin_user=self.admin)

        self.assertEqual(rejected, 1)
        user_badge = UserBadge.objects.get(user=self.user1, badge=self.badge)
        self.assertEqual(user_badge.status, UserBadge.STATUS_REJECTED)
        self.assertFalse(user_badge.is_awarded)

    def test_normal_sync_does_not_resubmit_rejected_badge(self):
        ModuleProgress.objects.create(user=self.user1, module=self.module1, completed=True)
        ModuleProgress.objects.create(user=self.user1, module=self.module2, completed=True)
        sync_user_badges(self.user1, admin_user=self.admin)
        auto_reject_pending_badges(self.badge, admin_user=self.admin)

        sync_user_badges(self.user1, admin_user=self.admin)

        user_badge = UserBadge.objects.get(user=self.user1, badge=self.badge)
        self.assertEqual(user_badge.status, UserBadge.STATUS_REJECTED)
        self.assertFalse(user_badge.is_awarded)

    def test_completed_enrollment_makes_course_badge_pending(self):
        course_badge = Badge.objects.create(
            name='Enrollment Completion',
            course=self.course,
            required_completed_modules=3,
            is_active=True,
        )
        CourseEnrollment.objects.create(
            user=self.user1,
            course=self.course,
            status='completed',
            total_chapters=3,
            completed_chapters=3,
            progress_percentage=100,
        )

        sync_user_badges(self.user1, admin_user=self.admin)

        user_badge = UserBadge.objects.get(user=self.user1, badge=course_badge)
        self.assertEqual(user_badge.status, UserBadge.STATUS_PENDING)
        self.assertFalse(user_badge.is_awarded)

    def test_auto_approve_pending_badges_notifies_user(self):
        ModuleProgress.objects.create(user=self.user1, module=self.module1, completed=True)
        ModuleProgress.objects.create(user=self.user1, module=self.module2, completed=True)
        sync_user_badges(self.user1, admin_user=self.admin)

        approved = auto_approve_pending_badges(self.badge, admin_user=self.admin)

        self.assertEqual(approved, 1)
        user_badge = UserBadge.objects.get(user=self.user1, badge=self.badge)
        self.assertEqual(user_badge.status, UserBadge.STATUS_GRANTED)
        self.assertTrue(
            UserNotification.objects.filter(
                user=self.user1,
                notification__title=f'Badge granted: {self.badge.name}',
            ).exists()
        )

    def test_major_badge_is_auto_granted_after_required_badges_are_earned(self):
        course_two = Course.objects.create(title={'en': 'Second Course'})
        other_module = Module.objects.create(course=course_two, title={'en': 'M1'})

        badge_one = Badge.objects.create(
            name='Badge Course Completion',
            course=self.course,
            required_completed_modules=2,
            is_active=True,
        )
        badge_two = Badge.objects.create(
            name='Second Course Completion',
            course=course_two,
            required_completed_modules=1,
            is_active=True,
        )
        major_badge = Badge.objects.create(
            name='Training Starter',
            is_major_badge=True,
            required_badges_count=2,
            required_completed_modules=0,
            auto_approve_when_eligible=True,
            is_active=True,
        )

        ModuleProgress.objects.create(user=self.user1, module=self.module1, completed=True)
        ModuleProgress.objects.create(user=self.user1, module=self.module2, completed=True)
        ModuleProgress.objects.create(user=self.user1, module=other_module, completed=True)

        sync_user_badges(self.user1, admin_user=self.admin)
        auto_approve_pending_badges(badge_one, admin_user=self.admin)
        auto_approve_pending_badges(badge_two, admin_user=self.admin)

        major_user_badge = UserBadge.objects.get(user=self.user1, badge=major_badge)
        self.assertEqual(major_user_badge.status, UserBadge.STATUS_GRANTED)
        self.assertTrue(major_user_badge.is_awarded)


class BadgeApiTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='apiuser@example.com',
            username='apiuser',
            password='password123',
        )
        self.client.force_authenticate(user=self.user)

        self.course = Course.objects.create(title={'en': 'API Course'})
        self.module = Module.objects.create(course=self.course, title={'en': 'Module A'})

        self.badge = Badge.objects.create(
            name='API Badge',
            course=self.course,
            required_completed_modules=1,
            is_active=True,
        )

    def test_badges_endpoint_returns_in_progress_for_new_user(self):
        url = reverse('badge-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'API Badge')
        self.assertEqual(response.data[0]['status'], UserBadge.STATUS_IN_PROGRESS)
        self.assertTrue(response.data[0]['in_progress'])
        self.assertEqual(response.data[0]['progress_current'], 0)
        self.assertEqual(response.data[0]['progress_required'], 1)
        self.assertEqual(response.data[0]['progress_kind'], 'modules')
        self.assertIsNotNone(response.data[0]['user_badge_id'])

    def test_badges_endpoint_compact_omits_expensive_translation_lists(self):
        response = self.client.get(f'{reverse("badge-list")}?compact=1')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('name_translations', response.data[0])
        self.assertNotIn('description_translations', response.data[0])
        self.assertNotIn('skills_awarded', response.data[0])
        self.assertNotIn('skills_awarded_translations', response.data[0])
        self.assertNotIn('lesson_highlights', response.data[0])
        self.assertNotIn('lesson_highlights_translations', response.data[0])
        self.assertNotIn('course_title_translations', response.data[0])
        self.assertIn('progress_current', response.data[0])

    def test_badges_endpoint_returns_requested_localized_fields(self):
        self.badge.name_translations = {
            'en': 'API Badge',
            'ms': 'Lencana API',
            'zh': 'API 徽章',
        }
        self.badge.description_translations = {
            'en': 'English description',
            'ms': 'Penerangan Melayu',
            'zh': '中文说明',
        }
        self.badge.skills_awarded = [
            {'en': 'English Skill', 'ms': 'Kemahiran Melayu', 'zh': '中文技能'},
        ]
        self.badge.save()

        response = self.client.get(f'{reverse("badge-list")}?compact=1&lang=ms')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['localized_name'], 'Lencana API')
        self.assertEqual(response.data[0]['localized_description'], 'Penerangan Melayu')
        self.assertEqual(response.data[0]['localized_skills_awarded'], ['Kemahiran Melayu'])

    def test_badges_endpoint_returns_pending_when_requirement_met(self):
        ModuleProgress.objects.create(user=self.user, module=self.module, completed=True)

        url = f'{reverse("badge-list")}?sync=1'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['status'], UserBadge.STATUS_PENDING)
        self.assertTrue(response.data[0]['pending'])
        self.assertEqual(response.data[0]['progress_current'], 1)
        self.assertTrue(response.data[0]['eligible'])

    def test_badges_endpoint_sync_does_not_create_staff_notifications(self):
        staff = CustomUser.objects.create_user(
            email='staff@example.com',
            username='staff',
            password='password123',
            is_staff=True,
        )
        chapter = Chapter.objects.create(course=self.course, title={'en': 'Chapter 1'}, order=1)
        ChapterProgress.objects.create(
            user=self.user,
            chapter=chapter,
            is_complete=True,
            completed_lessons=1,
            total_lessons=1,
            progress_percentage=100,
        )

        response = self.client.get(f'{reverse("badge-list")}?sync=1')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['status'], UserBadge.STATUS_PENDING)
        self.assertFalse(
            UserNotification.objects.filter(
                user=staff,
                notification__title__icontains='Badge approval needed',
            ).exists()
        )

    def test_my_badges_endpoint_returns_awarded_badges(self):
        ModuleProgress.objects.create(user=self.user, module=self.module, completed=True)
        sync_user_badges(self.user)
        auto_approve_pending_badges(self.badge)

        url = reverse('my-badge-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['badge_name'], 'API Badge')


class BadgeRegistrationTests(APITestCase):
    def setUp(self):
        self.badge = Badge.objects.create(
            name='Welcome Badge',
            required_completed_modules=1,
            is_active=True,
        )

    def test_registration_creates_in_progress_badge_rows_for_new_user(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'password123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = CustomUser.objects.get(email='newuser@example.com')
        user_badge = UserBadge.objects.get(user=user, badge=self.badge)

        self.assertEqual(user_badge.status, UserBadge.STATUS_IN_PROGRESS)
        self.assertFalse(user_badge.is_awarded)
