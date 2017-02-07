# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-07 06:41
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0018_course_cntype'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='event_type',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='prices',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
    ]
