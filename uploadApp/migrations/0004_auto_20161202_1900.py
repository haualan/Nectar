# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-02 19:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uploadApp', '0003_project_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='isPublic',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterUniqueTogether(
            name='project',
            unique_together=set([]),
        ),
    ]
