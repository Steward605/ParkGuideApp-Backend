from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from user_progress.models import Badge


class DashboardBadgeSaveTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='password123',
            is_staff=True,
        )
        self.client.force_login(self.admin)
        self.url = reverse('dashboard:badges')

    def test_save_badge_without_badge_id_updates_existing_badge_with_same_name(self):
        badge = Badge.objects.create(
            name='Park Guide Fundamentals Completion Badge',
            description='Old description',
            required_completed_modules=1,
            is_active=True,
        )

        response = self.client.post(
            self.url,
            {
                'action': 'save_badge',
                'name': 'Park Guide Fundamentals Completion Badge',
                'description': 'Updated description',
                'required_completed_modules': '3',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Badge.objects.filter(name=badge.name).count(), 1)

        badge.refresh_from_db()
        self.assertEqual(badge.description, 'Updated description')
        self.assertEqual(badge.required_completed_modules, 3)

    def test_save_badge_rejects_renaming_badge_to_an_existing_name(self):
        existing = Badge.objects.create(
            name='Existing Badge',
            required_completed_modules=1,
            is_active=True,
        )
        target = Badge.objects.create(
            name='Target Badge',
            required_completed_modules=1,
            is_active=True,
        )

        response = self.client.post(
            self.url,
            {
                'action': 'save_badge',
                'badge_id': str(target.id),
                'name': existing.name,
                'description': 'Should not save',
                'required_completed_modules': '2',
            },
        )

        self.assertEqual(response.status_code, 302)

        target.refresh_from_db()
        self.assertEqual(target.name, 'Target Badge')
        self.assertEqual(target.required_completed_modules, 1)
