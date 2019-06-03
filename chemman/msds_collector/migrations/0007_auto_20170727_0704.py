# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-27 05:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('msds_collector', '0006_auto_20170726_1108'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parseddata',
            name='euh',
            field=models.CharField(blank=True, help_text='Separate with ",".', max_length=100, verbose_name='EUH'),
        ),
        migrations.AlterField(
            model_name='parseddata',
            name='h',
            field=models.CharField(blank=True, help_text='Separate with ",".', max_length=200, verbose_name='H'),
        ),
        migrations.AlterField(
            model_name='parseddata',
            name='p',
            field=models.CharField(blank=True, help_text='Separate with ",".', max_length=200, verbose_name='P'),
        ),
    ]