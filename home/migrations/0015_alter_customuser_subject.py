# Generated by Django 5.1 on 2024-08-15 06:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0014_alter_classroom_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='home.subjects'),
        ),
    ]
