# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-02 15:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0006_auto_20161122_1724'),
        ('uploadApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectIconFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='uploadApp.Project')),
                ('userFile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='profiles.UserFile')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='projectpackagefile',
            unique_together=set([('project',)]),
        ),
        migrations.AlterUniqueTogether(
            name='projecticonfile',
            unique_together=set([('project',)]),
        ),
    ]
