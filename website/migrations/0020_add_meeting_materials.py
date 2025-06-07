from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0019_add_recording_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='materials',
            field=models.FileField(blank=True, null=True, upload_to='meeting_materials/', verbose_name='مواد الاجتماع'),
        ),
    ]
