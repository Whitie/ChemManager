# Generated by Django 2.2.15 on 2021-10-15 06:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0010_auto_20211013_1202'),
    ]

    operations = [
        migrations.AddField(
            model_name='storedpackage',
            name='delivered_for',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='my_deliveries', to=settings.AUTH_USER_MODEL, verbose_name='Delivered for'),
        ),
    ]
