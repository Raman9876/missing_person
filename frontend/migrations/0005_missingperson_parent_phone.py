# Generated by Django 5.1.7 on 2025-03-21 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0004_missingperson_face_encoding'),
    ]

    operations = [
        migrations.AddField(
            model_name='missingperson',
            name='parent_phone',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]
