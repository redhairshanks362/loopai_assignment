# Generated by Django 4.2.5 on 2023-09-23 04:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store_monitor', '0006_store_status'),
    ]

    operations = [
        migrations.DeleteModel(
            name='store_status',
        ),
    ]
