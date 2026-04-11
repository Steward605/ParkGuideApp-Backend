from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.services import send_push_notification, send_push_to_users
from notifications.models import PushToken

User = get_user_model()

class Command(BaseCommand):
    help = 'Test sending push notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to send test notification to',
        )
        parser.add_argument(
            '--token',
            type=str,
            help='Specific push token to test',
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Send to all users with registered tokens',
        )

    def handle(self, *args, **options):
        if options.get('token'):
            # Test with specific token
            self.stdout.write(f"Sending test notification to token: {options['token']}")
            result = send_push_notification(
                tokens=[options['token']],
                title="Park Guide Test",
                body="This is a test push notification",
                data={'test': 'true'}
            )
            self.stdout.write(self.style.SUCCESS(f"Result: {result}"))

        elif options.get('user_id'):
            # Test with specific user
            user_id = options['user_id']
            try:
                user = User.objects.get(id=user_id)
                tokens = PushToken.objects.filter(user=user, is_active=True).values_list('token', flat=True)
                if tokens:
                    self.stdout.write(f"Sending to user {user.username} ({len(tokens)} tokens)")
                    result = send_push_to_users(
                        users=[user],
                        title="Park Guide Test",
                        description="This is a test push notification from the backend",
                    )
                    self.stdout.write(self.style.SUCCESS(f"Result: {result}"))
                else:
                    self.stdout.write(self.style.WARNING(f"User {user.username} has no registered tokens"))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found"))

        elif options.get('all_users'):
            # Send to all users with tokens
            users_with_tokens = User.objects.filter(push_tokens__is_active=True).distinct()
            self.stdout.write(f"Sending test notification to {users_with_tokens.count()} users")
            
            result = send_push_to_users(
                users=users_with_tokens,
                title="Park Guide System Test",
                description="This is a system test notification",
            )
            self.stdout.write(self.style.SUCCESS(f"Result: {result}"))

        else:
            # List all registered tokens
            tokens_count = PushToken.objects.filter(is_active=True).count()
            self.stdout.write(f"\nRegistered Push Tokens: {tokens_count}")
            
            for token in PushToken.objects.filter(is_active=True).select_related('user'):
                self.stdout.write(f"  {token.user.username} ({token.device_type}): {token.token[:20]}...")
            
            self.stdout.write("\nUsage:")
            self.stdout.write("  Send to user:    python manage.py test_push_notification --user-id <id>")
            self.stdout.write("  Send to token:   python manage.py test_push_notification --token <token>")
            self.stdout.write("  Send to all:     python manage.py test_push_notification --all-users")
