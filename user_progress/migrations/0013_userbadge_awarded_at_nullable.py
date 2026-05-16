from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_progress', '0012_badge_translations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userbadge',
            name='awarded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
