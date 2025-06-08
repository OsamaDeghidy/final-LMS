from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0023_remove_monitor_model'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='meeting',
            name='school',
        ),
    ]
