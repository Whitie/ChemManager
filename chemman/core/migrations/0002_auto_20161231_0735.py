# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-12-31 07:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chemical',
            name='wiki_link',
            field=models.CharField(blank=True, max_length=300, verbose_name='Wikipedia Link'),
        ),
    ]
