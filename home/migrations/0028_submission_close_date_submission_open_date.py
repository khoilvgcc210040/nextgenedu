# Generated by Django 5.1 on 2024-08-16 10:11

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0027_rename_grade_studentfile_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='close_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='submission',
            name='open_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
