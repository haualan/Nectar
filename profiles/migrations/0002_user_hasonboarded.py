# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-07 18:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='hasOnboarded',
            field=models.BooleanField(default=False),
        ),
    ]
