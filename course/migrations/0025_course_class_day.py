# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-09 10:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0024_course_subdomain'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='class_day',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
