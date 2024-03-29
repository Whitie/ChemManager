# Generated by Django 2.2.9 on 2020-01-30 14:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import operating_instruction_creator.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0008_auto_20200124_1320'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProtectionPictogram',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ident', models.CharField(max_length=10, verbose_name='Identifier')),
                ('icon', models.FileField(upload_to='oic')),
            ],
            options={
                'verbose_name': 'Protection Pictogram',
                'verbose_name_plural': 'Protection Pictograms',
                'ordering': ['ident'],
            },
        ),
        migrations.CreateModel(
            name='WorkDepartment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Work Department',
                'verbose_name_plural': 'Work Departments',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='OperatingInstructionDraft',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hazards', models.TextField(default='-', verbose_name='Hazards for people and the environment')),
                ('protection', models.TextField(default='-', verbose_name='Protective measures and rules of conduct')),
                ('eye_protection', models.CharField(max_length=30, verbose_name='Eye protection')),
                ('hand_protection', models.CharField(max_length=30, verbose_name='Hand protection')),
                ('conduct', models.TextField(default='-', verbose_name='Conduct in case of danger')),
                ('first_aid', models.TextField(default='-', verbose_name='First aid')),
                ('skin', models.CharField(default='-', max_length=150, verbose_name='After skin contact')),
                ('eye', models.CharField(default='-', max_length=150, verbose_name='After eye contact')),
                ('breathe', models.CharField(default='-', max_length=150, verbose_name='After breathe in')),
                ('swallow', models.CharField(default='-', max_length=150, verbose_name='After swallow')),
                ('disposal', models.TextField(default='-', verbose_name='Proper disposal')),
                ('ext_phone', models.CharField(default='0-112', max_length=20, verbose_name='External help number')),
                ('int_phone', models.CharField(default='10', max_length=20, verbose_name='Internal help number')),
                ('language', models.CharField(default='de', max_length=5, verbose_name='Language')),
                ('chemical', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='operating_instruction_drafts', to='core.Chemical', verbose_name='Chemical')),
                ('protection_pics', models.ManyToManyField(to='operating_instruction_creator.ProtectionPictogram', verbose_name='Protection Pictograms')),
                ('responsible', models.ForeignKey(on_delete=models.SET(operating_instruction_creator.models.get_sentinel_user), related_name='drafts', to=settings.AUTH_USER_MODEL, verbose_name='Responsible')),
                ('signature', models.ForeignKey(on_delete=models.SET(operating_instruction_creator.models.get_sentinel_user), related_name='sig_drafts', to=settings.AUTH_USER_MODEL, verbose_name='Signature')),
                ('work_departments', models.ManyToManyField(related_name='operating_instruction_drafts', to='operating_instruction_creator.WorkDepartment', verbose_name='Work Departments')),
            ],
            options={
                'verbose_name': 'Operating instruction draft',
                'verbose_name_plural': 'Operating instruction drafts',
                'ordering': ['chemical__name'],
                'permissions': (('create', 'Can create operating instructions'), ('release', 'Can release operating instructions')),
            },
        ),
    ]
