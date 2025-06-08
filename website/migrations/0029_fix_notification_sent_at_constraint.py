from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0028_fix_notification_sent_at'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE website_notification_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                notification_type VARCHAR(20) NOT NULL,
                scheduled_time DATETIME NOT NULL,
                sent BOOLEAN NOT NULL,
                sent_at DATETIME NULL,
                is_read BOOLEAN NOT NULL,
                meeting_id INTEGER NOT NULL REFERENCES website_meeting(id) DEFERRABLE INITIALLY DEFERRED
            );
            
            INSERT INTO website_notification_new (
                id, message, notification_type, scheduled_time, sent, sent_at, is_read, meeting_id
            ) SELECT 
                id, message, notification_type, scheduled_time, sent, sent_at, is_read, meeting_id 
              FROM website_notification;
              
            DROP TABLE website_notification;
            ALTER TABLE website_notification_new RENAME TO website_notification;
            
            CREATE INDEX website_notification_meeting_id_4f0c0b9a ON website_notification (meeting_id);
            """,
            reverse_sql="""
            -- No reverse needed as this is fixing a forward migration issue
            """
        ),
    ]
