# Generated by Django 5.1 on 2024-08-16 08:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0017_submission'),
    ]

    operations = [
        migrations.RenameField(
            model_name='section',
            old_name='name',
            new_name='title',
        ),
        migrations.DeleteModel(
            name='Submission',
        ),
    ]
