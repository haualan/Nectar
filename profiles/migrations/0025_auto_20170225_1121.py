# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-25 11:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0024_auto_20170225_1117'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ledger',
            name='stripeAcct',
            field=models.CharField(choices=[(b'sgd', b'sgd'), (b'hkd', b'hkd'), (b'ntd', b'ntd')], max_length=30, null=True),
        ),
    ]
