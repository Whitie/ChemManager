# Generated by Django 2.2.9 on 2020-02-05 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operating_instruction_creator', '0002_auto_20200203_1314'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operatinginstructiondraft',
            name='eye_protection',
            field=models.CharField(max_length=60, verbose_name='Eye protection'),
        ),
        migrations.AlterField(
            model_name='operatinginstructiondraft',
            name='hand_protection',
            field=models.CharField(max_length=60, verbose_name='Hand protection'),
        ),
    ]
