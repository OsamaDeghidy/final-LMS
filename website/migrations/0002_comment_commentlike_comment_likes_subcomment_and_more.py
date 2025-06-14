# Generated by Django 5.2.1 on 2025-06-15 05:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='محتوى التعليق')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='website.course')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_comments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'تعليق',
                'verbose_name_plural': 'التعليقات',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CommentLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.comment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'إعجاب بالتعليق',
                'verbose_name_plural': 'إعجابات التعليقات',
                'unique_together': {('user', 'comment')},
            },
        ),
        migrations.AddField(
            model_name='comment',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='liked_comments', through='website.CommentLike', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='SubComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='محتوى الرد')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='website.comment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comment_replies', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'رد',
                'verbose_name_plural': 'الردود',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='SubCommentLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('subcomment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.subcomment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'إعجاب بالرد',
                'verbose_name_plural': 'إعجابات الردود',
                'unique_together': {('user', 'subcomment')},
            },
        ),
        migrations.AddField(
            model_name='subcomment',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='liked_subcomments', through='website.SubCommentLike', to=settings.AUTH_USER_MODEL),
        ),
    ]
