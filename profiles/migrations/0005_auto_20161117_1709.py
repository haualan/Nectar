# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-17 17:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_auto_20161116_2335'),
    ]

    operations = [
        migrations.AddField(
            model_name='userschoolrelation',
            name='enrollmentDate',
            field=models.DateField(blank=True, default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='school',
            name='lat',
            field=models.DecimalField(decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AlterField(
            model_name='school',
            name='lon',
            field=models.DecimalField(decimal_places=6, max_digits=9, null=True),
        ),
    ]
