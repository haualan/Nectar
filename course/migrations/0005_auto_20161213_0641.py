# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-13 06:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0004_trophy_language'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trophy',
            name='language',
            field=models.CharField(choices=[('', 'None'), ('PYTHON', 'Python'), ('MINECRAFT', 'Minecraft'), ('3DPRINTING', '3DPrinting'), ('APPINVENTOR', 'AppInventor'), ('SCRATCH', 'Scratch'), ('JAVA', 'Java'), ('JS', 'JavaScript')], default='', max_length=20),
        ),
    ]
