from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('website', '0024_remove_meeting_school'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('DAY_BEFORE', 'قبل يوم'), ('HOUR_BEFORE', 'قبل ساعة'), ('CANCELLED', 'تم الإلغاء'), ('RESCHEDULED', 'تم إعادة الجدولة'), ('CUSTOM', 'مخصص')], default='CUSTOM', max_length=20, verbose_name='نوع الإشعار'),
        ),
    ]
