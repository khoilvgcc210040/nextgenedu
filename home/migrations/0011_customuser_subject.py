# Generated by Django 5.1 on 2024-08-15 05:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0010_classroom_created_at_classroom_likes_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='subject',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
