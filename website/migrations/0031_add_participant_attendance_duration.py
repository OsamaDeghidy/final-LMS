from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0030_add_participant_exit_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='attendance_duration',
            field=models.DurationField(blank=True, null=True, verbose_name='مدة الحضور'),
        ),
    ]
