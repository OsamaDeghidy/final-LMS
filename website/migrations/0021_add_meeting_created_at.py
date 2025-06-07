from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0020_add_meeting_materials'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='تاريخ الإنشاء'),
            preserve_default=False,
        ),
    ]
