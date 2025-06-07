from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0018_delete_teacherapplication'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='recording_url',
            field=models.URLField(blank=True, null=True, verbose_name='رابط التسجيل'),
        ),
    ]
