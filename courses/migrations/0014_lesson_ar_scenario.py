from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ar_training', '0002_rebuild_scoped_training_tables'),
        ('courses', '0013_course_type_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='ar_scenario',
            field=models.ForeignKey(
                blank=True,
                help_text='Optional AR/VR scenario attached to this normal course lesson',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='course_lessons',
                to='ar_training.arscenario',
            ),
        ),
    ]
