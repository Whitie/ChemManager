# Generated by Django 2.2.10 on 2020-02-17 11:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('msds_collector', '0010_auto_20200124_1320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parseddata',
            name='whc',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(0, '0 - Non-hazardous to water'), (1, '1 - Low hazard to waters'), (2, '2 - Hazard to waters'), (3, '3 - Severe hazard to waters')], default=0, help_text='Water Hazard Class', null=True, verbose_name='WHC'),
        ),
    ]
