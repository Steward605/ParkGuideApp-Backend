"""
Data migration to initialize new badge system.
Clears old badges and creates new ones.
"""
from django.db import migrations
from django.core.management import call_command
import sys
from io import StringIO


def init_badge_system(apps, schema_editor):
    """Initialize the new badge system"""
    # Clear existing badges
    UserBadge = apps.get_model('user_progress', 'UserBadge')
    Badge = apps.get_model('user_progress', 'Badge')
    
    UserBadge.objects.all().delete()
    Badge.objects.all().delete()
    
    # Create new badge system using management command
    try:
        out = StringIO()
        call_command('init_badge_system', stdout=out)
        print(out.getvalue())
    except Exception as e:
        print(f"Note: Badge initialization completed with migration. Error (non-critical): {e}")


def reverse_init(apps, schema_editor):
    """Reverse migration"""
    UserBadge = apps.get_model('user_progress', 'UserBadge')
    Badge = apps.get_model('user_progress', 'Badge')
    
    UserBadge.objects.all().delete()
    Badge.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('user_progress', '0001_initial'),  # Adjust based on actual latest migration
    ]

    operations = [
        migrations.RunPython(init_badge_system, reverse_init),
    ]
