# Generated by Django 5.1 on 2024-08-20 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0036_alter_quizresult_answered_questions_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='classroom',
            name='average_rating',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=3),
        ),
    ]
