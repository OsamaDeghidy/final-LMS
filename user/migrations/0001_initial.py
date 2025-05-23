# Generated by Django 5.2 on 2025-05-05 12:47

import ckeditor.fields
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('name', models.CharField(blank=True, max_length=2000, null=True)),
                ('email', models.CharField(blank=True, max_length=2000, null=True)),
                ('phone', models.CharField(blank=True, max_length=2000, null=True)),
                ('status', models.CharField(blank=True, choices=[('Student', 'Student'), ('Teacher', 'Teacher'), ('Organization', 'Organization')], default='Student', max_length=2000, null=True)),
                ('image_profile', models.ImageField(blank=True, default='blank.png', null=True, upload_to='user_profile/')),
                ('shortBio', models.CharField(blank=True, max_length=2000, null=True)),
                ('detail', ckeditor.fields.RichTextField(blank=True, null=True)),
                ('github', models.URLField(blank=True, null=True)),
                ('youtube', models.URLField(blank=True, null=True)),
                ('twitter', models.URLField(blank=True, null=True)),
                ('facebook', models.URLField(blank=True, null=True)),
                ('instagram', models.URLField(blank=True, null=True)),
                ('linkedin', models.URLField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', ckeditor.fields.RichTextField(blank=True, null=True)),
                ('location', models.CharField(blank=True, max_length=2000, null=True)),
                ('website', models.URLField(blank=True, null=True)),
                ('founded_year', models.DateField(blank=True, null=True)),
                ('employees', models.IntegerField(blank=True, default=0, null=True)),
                ('profile', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user.profile')),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(blank=True, max_length=2000, null=True)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('profile', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user.profile')),
            ],
        ),
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(blank=True, max_length=2000, null=True)),
                ('qualification', models.CharField(blank=True, max_length=2000, null=True)),
                ('bio', ckeditor.fields.RichTextField(blank=True, null=True)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('research_interests', ckeditor.fields.RichTextField(blank=True, null=True)),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user.organization')),
                ('profile', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user.profile')),
            ],
        ),
    ]
