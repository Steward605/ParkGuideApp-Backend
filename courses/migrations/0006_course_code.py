# Generated migration to add code field to Course

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_module_code'),
    ]

    operations = [
        # Step 1: Add the field as nullable (no unique constraint yet)
        migrations.AddField(
            model_name='course',
            name='code',
            field=models.CharField(blank=True, help_text="Course code (e.g., 'course1')", max_length=20, null=True),
        ),
    ]
