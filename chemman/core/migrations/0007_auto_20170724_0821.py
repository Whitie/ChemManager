# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-24 06:21
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20170213_1154'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='storage',
            options={'ordering': ['department__name', 'name'], 'permissions': (('can_store', 'Can store chemicals'), ('can_consume', 'Can consume chemicals'), ('can_transfer', 'Can transfer chemicals'), ('can_dispose', 'Can dispose chemicals'), ('set_limits', 'Can set stocklimits'), ('manage_storage', 'Can manage chemicals, limits...'), ('inventory', 'Can make inventory')), 'verbose_name': 'Storage', 'verbose_name_plural': 'Storages'},
        ),
    ]
