from django.db import migrations, models


def seed_badge_translations(apps, schema_editor):
    Badge = apps.get_model('user_progress', 'Badge')
    for badge in Badge.objects.all():
        if not badge.name_translations:
            badge.name_translations = {'en': badge.name or ''}
        if not badge.description_translations:
            badge.description_translations = {'en': badge.description or ''}
        badge.save(update_fields=['name_translations', 'description_translations'])


class Migration(migrations.Migration):

    dependencies = [
        ('user_progress', '0011_badge_badge_image_source_badge_badge_image_url_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='badge',
            name='description_translations',
            field=models.JSONField(blank=True, default=dict, help_text='Multilingual badge description {en, ms, zh}'),
        ),
        migrations.AddField(
            model_name='badge',
            name='name_translations',
            field=models.JSONField(blank=True, default=dict, help_text='Multilingual badge name {en, ms, zh}'),
        ),
        migrations.RunPython(seed_badge_translations, migrations.RunPython.noop),
    ]
