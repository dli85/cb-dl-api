# Generated by Django 5.1.6 on 2025-02-20 04:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comics", "0002_page_page_number"),
    ]

    operations = [
        migrations.AlterField(
            model_name="page",
            name="image_link",
            field=models.URLField(max_length=500, unique=True),
        ),
    ]
