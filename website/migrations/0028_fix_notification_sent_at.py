from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0027_fix_notification_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='sent_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='وقت الإرسال'),
        ),
    ]
