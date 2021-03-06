# Generated by Django 2.2.9 on 2020-02-03 12:14

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('operating_instruction_creator', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='operatinginstructiondraft',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Created'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='operatinginstructiondraft',
            name='edited',
            field=models.DateTimeField(auto_now=True, verbose_name='Created'),
        ),
        migrations.AddField(
            model_name='operatinginstructiondraft',
            name='green_cross',
            field=models.BooleanField(default=True, verbose_name='Green Cross'),
        ),
        migrations.AddField(
            model_name='operatinginstructiondraft',
            name='released',
            field=models.DateField(blank=True, default=None, editable=False, null=True, verbose_name='Released'),
        ),
    ]
