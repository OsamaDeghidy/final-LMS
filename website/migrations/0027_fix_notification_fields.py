from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0026_add_scheduled_time'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='notification',
                    name='sent',
                    field=models.BooleanField(default=False, verbose_name='تم الإرسال'),
                ),
                migrations.AddField(
                    model_name='notification',
                    name='sent_at',
                    field=models.DateTimeField(blank=True, null=True, verbose_name='وقت الإرسال'),
                ),
            ],
            database_operations=[],
        )
    ]

    def apply(self, project_state, schema_editor, collect_sql=False):
        # Check if columns exist before adding them
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(website_notification);")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'sent' not in columns:
                cursor.execute("ALTER TABLE website_notification ADD COLUMN sent BOOLEAN DEFAULT 0 NOT NULL;")
            
            if 'sent_at' not in columns:
                cursor.execute("ALTER TABLE website_notification ADD COLUMN sent_at DATETIME NULL;")
        
        return project_state
