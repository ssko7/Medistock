# Generated by Django 4.2.19 on 2025-06-20 09:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('b', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='batch',
            name='hsn_code',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
