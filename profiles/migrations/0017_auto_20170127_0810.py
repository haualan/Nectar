# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-27 08:10
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0018_course_cntype'),
        ('profiles', '0016_user_heardfromoption'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=255, unique=True)),
                ('description_public', models.TextField(blank=True)),
                ('description_internal', models.TextField(blank=True)),
                ('effectDollar', models.DecimalField(decimal_places=6, default=0, max_digits=9)),
                ('effectMultiplier', models.DecimalField(decimal_places=6, default=1.0, max_digits=9)),
                ('lastModified', models.DateTimeField(auto_now=True)),
                ('validFrom', models.DateTimeField(default=django.utils.timezone.now, null=True)),
                ('validTo', models.DateTimeField(default=None, null=True)),
                ('timerSeconds', models.IntegerField(default=None, null=True)),
                ('maxUses', models.IntegerField(default=None, null=True)),
                ('isValidForAll', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='CouponCourseRelation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='profiles.Coupon')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='course.Course')),
            ],
        ),
        migrations.CreateModel(
            name='CouponUserRelation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('isUsed', models.BooleanField(default=False)),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='profiles.Coupon')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Ledger',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rawData', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('event_id', models.CharField(max_length=255, null=True, unique=True)),
                ('event_type', models.CharField(choices=[(b'charge.succeeded', b'charge.succeeded'), (b'charge.refunded', b'charge.refunded')], max_length=255)),
                ('amount', models.IntegerField(default=0)),
                ('amount_refunded', models.IntegerField(default=0)),
                ('livemode', models.BooleanField(default=False)),
                ('transactionDateTime', models.DateTimeField(default=django.utils.timezone.now)),
                ('currency', models.CharField(max_length=3)),
                ('stripeCustomerId', models.CharField(max_length=255, null=True)),
                ('buyerID', models.CharField(max_length=255)),
                ('studentID', models.CharField(max_length=255)),
                ('course_code', models.CharField(max_length=255)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='couponcourserelation',
            unique_together=set([('coupon', 'course')]),
        ),
    ]