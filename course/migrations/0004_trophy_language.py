# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-12 09:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0003_auto_20161128_1539'),
    ]

    operations = [
        migrations.AddField(
            model_name='trophy',
            name='language',
            field=models.CharField(choices=[('PYTHON', 'Python'), ('MINECRAFT', 'Minecraft'), ('3DPRINTING', '3DPrinting'), ('APPINVENTOR', 'AppInventor'), ('SCRATCH', 'Scratch'), ('JAVA', 'Java'), ('JS', 'JavaScript')], default=None, max_length=20, null=True),
        ),
    ]
