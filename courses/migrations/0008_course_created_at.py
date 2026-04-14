# Generated migration to add created_at field to Course model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0007_new_course_catalog_system'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, blank=True),
        ),
    ]
