# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-28 08:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('msds_collector', '0008_auto_20170727_0907'),
    ]

    operations = [
        migrations.AddField(
            model_name='parseddata',
            name='structure_fn',
            field=models.CharField(blank=True, max_length=200, verbose_name='Filename'),
        ),
    ]