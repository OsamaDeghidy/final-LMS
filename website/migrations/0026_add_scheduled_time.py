from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0025_add_notification_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='scheduled_time',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='وقت الجدولة'),
            preserve_default=False,
        ),
    ]
