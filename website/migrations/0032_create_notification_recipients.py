from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0031_add_participant_attendance_duration'),
    ]

    operations = [
migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='NotificationRecipients',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.notification')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'website_notification_recipients',
                        'unique_together': {('notification', 'user')},
                    },
                ),
                migrations.AddField(
                    model_name='notification',
                    name='recipients',
                    field=models.ManyToManyField(related_name='meeting_notifications', through='website.NotificationRecipients', to=settings.AUTH_USER_MODEL, verbose_name='المستلمون'),
                ),
            ],
            database_operations=[],
        ),
    ]
