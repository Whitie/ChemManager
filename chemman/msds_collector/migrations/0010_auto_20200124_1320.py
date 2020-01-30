# Generated by Django 2.2.9 on 2020-01-24 12:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('msds_collector', '0009_parseddata_structure_fn'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadedmsds',
            name='in_progress',
            field=models.BooleanField(default=False, verbose_name='In Progress'),
        ),
        migrations.AlterField(
            model_name='uploadedmsds',
            name='added_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploads', to=settings.AUTH_USER_MODEL, verbose_name='Added by'),
        ),
    ]