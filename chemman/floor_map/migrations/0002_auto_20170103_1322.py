# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-03 12:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('floor_map', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='floor',
            options={'ordering': ['building', '-level'], 'verbose_name': 'Floor', 'verbose_name_plural': 'Floors'},
        ),
        migrations.AddField(
            model_name='floorstorage',
            name='floor',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='storages', to='floor_map.Floor', verbose_name='Floor'),
            preserve_default=False,
        ),
    ]
