# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-13 06:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0015_auto_20170113_0628'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='course',
            unique_together=set([('course_code', 'eventbrite_tag')]),
        ),
    ]
