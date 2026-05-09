from django.db import migrations, models


def infer_course_type(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')

    for course in Course.objects.all():
        has_prerequisites = course.prerequisites.exists()
        title = course.title or {}
        text = " ".join([
            str(course.code or ""),
            str(title.get("en", "")),
            str((course.description or {}).get("en", "")),
        ]).lower()
        is_park_specific = has_prerequisites or "bako" in text or "park-specific" in text or "ar " in text
        course.course_type = "park_specific" if is_park_specific else "general"
        if not isinstance(course.tags, list):
            course.tags = []
        course.save(update_fields=["course_type", "tags"])


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0012_alter_chapterprogress_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='course_type',
            field=models.CharField(
                choices=[('general', 'General'), ('park_specific', 'Park Specific')],
                default='general',
                help_text='General courses unlock park-specific courses when all general courses are complete.',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='course',
            name='tags',
            field=models.JSONField(blank=True, default=list, help_text='Course/material tags used by apps and dashboards'),
        ),
        migrations.RunPython(infer_course_type, migrations.RunPython.noop),
    ]
