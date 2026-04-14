# Generated migration to add code field to Module

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_replace_quizprogress_with_courseprogress'),
    ]

    operations = [
        # Step 1: Add the field as nullable (no unique constraint yet)
        migrations.AddField(
            model_name='module',
            name='code',
            field=models.CharField(blank=True, help_text="Module code (e.g., '1.1', '1.2')", max_length=10, null=True),
        ),
    ]
