from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0021_add_meeting_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث'),
        ),
    ]
