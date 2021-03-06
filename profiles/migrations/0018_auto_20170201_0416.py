# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-01 04:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0017_auto_20170127_0810'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ledger',
            name='amount',
        ),
        migrations.RemoveField(
            model_name='ledger',
            name='amount_refunded',
        ),
        migrations.AddField(
            model_name='ledger',
            name='localCurrencyChargedAmount',
            field=models.DecimalField(decimal_places=6, default=0, max_digits=15),
        ),
        migrations.AddField(
            model_name='ledger',
            name='order_id',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='coupon',
            name='effectDollar',
            field=models.DecimalField(decimal_places=6, default=0, max_digits=15),
        ),
    ]
