from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0032_create_notification_recipients'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE TABLE IF NOT EXISTS website_notification_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id INTEGER NOT NULL REFERENCES website_notification(id) DEFERRABLE INITIALLY DEFERRED,
                user_id INTEGER NOT NULL REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED,
                UNIQUE(notification_id, user_id)
            );
            """,
            """
            DROP TABLE IF EXISTS website_notification_recipients;
            """
        ),
    ]
