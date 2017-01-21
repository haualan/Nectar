# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-20 06:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0013_user_stripecustomerid'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='formatted_address',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='school',
            name='place_id',
            field=models.CharField(max_length=255, null=True, unique=True),
        ),
    ]