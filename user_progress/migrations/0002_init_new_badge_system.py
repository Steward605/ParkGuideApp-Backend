"""
Data migration to initialize new badge system.
Clears old badges and creates new ones.
"""
from django.db import migrations


def init_badge_system(apps, schema_editor):
    """Seed a small legacy-safe badge without importing current models.

    This migration runs before later badge fields such as translations, course
    links, and approval status exist. Importing the management command here uses
    the current Badge model and can leave the migration transaction aborted on a
    fresh database, so keep this data step limited to the historical fields.
    """
    UserBadge = apps.get_model('user_progress', 'UserBadge')
    Badge = apps.get_model('user_progress', 'Badge')

    UserBadge.objects.all().delete()
    Badge.objects.all().delete()



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
