# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-04 12:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uploadApp', '0011_auto_20170104_1155'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='language',
            field=models.CharField(choices=[(b'PYTHON', b'Python'), (b'MINECRAFT', b'Minecraft'), (b'3DPRINTING', b'3DPrinting'), (b'APPINVENTOR', b'AppInventor'), (b'SCRATCH', b'Scratch'), (b'JAVA', b'Java'), (b'JS', b'JavaScript'), (b'UNITY', b'Unity'), (b'MBOT', b'mBot'), (b'SWIFT', b'Swift'), (b'HOPSCOTCH', b'Hopscotch'), (b'ROBOTICS', b'Robotics'), (b'SCRATCHX', b'ScratchX'), (b'OTHER', b'Other')], default='PYTHON', max_length=20),
        ),
    ]
