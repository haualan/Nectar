# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-23 08:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marketing',
            name='year',
            field=models.IntegerField(default=None, null=True),
        ),
    ]
