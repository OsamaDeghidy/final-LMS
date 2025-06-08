from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0029_fix_notification_sent_at_constraint'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='exit_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='وقت المغادرة'),
        ),
    ]
