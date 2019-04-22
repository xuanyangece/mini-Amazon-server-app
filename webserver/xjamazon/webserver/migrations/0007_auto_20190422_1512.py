# Generated by Django 2.2 on 2019-04-22 19:12

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webserver', '0006_auto_20190422_1343'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='id',
        ),
        migrations.AddField(
            model_name='package',
            name='date',
            field=models.DateTimeField(blank=True, default=datetime.datetime.now),
        ),
        migrations.AlterField(
            model_name='product',
            name='item_id',
            field=models.CharField(max_length=20, primary_key=True, serialize=False),
        ),
    ]
