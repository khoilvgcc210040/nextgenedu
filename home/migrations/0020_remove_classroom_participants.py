# Generated by Django 5.1 on 2024-08-16 08:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0019_submission'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='classroom',
            name='participants',
        ),
    ]
