from django.db import migrations, models


def infer_file_tags(apps, schema_editor):
    SecureFile = apps.get_model('secure_files', 'SecureFile')
    for item in SecureFile.objects.all():
        name = (item.original_name or '').lower()
        tags = []
        category = ''
        if any(token in name for token in ['guide', 'training', 'course']):
            category = 'Guide'
            tags.append('Guide')
        if any(token in name for token in ['policy', 'sop', 'procedure', 'rule']):
            category = category or 'Policy'
            tags.append('Policy')
        item.category = category
        item.tags = list(dict.fromkeys(tags))
        item.save(update_fields=['category', 'tags'])


class Migration(migrations.Migration):

    dependencies = [
        ('secure_files', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='securefile',
            name='category',
            field=models.CharField(blank=True, default='', max_length=80),
        ),
        migrations.AddField(
            model_name='securefile',
            name='tags',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(infer_file_tags, migrations.RunPython.noop),
    ]
