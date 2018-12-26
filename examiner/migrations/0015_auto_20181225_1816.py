# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-12-25 17:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('examiner', '0014_auto_20181224_1257'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='exam',
            options={'ordering': ('course_code', '-year', '-solutions')},
        ),
        migrations.AddField(
            model_name='pdf',
            name='exam',
            field=models.ForeignKey(help_text='Hvilket eksamenssett PDFen trolig inneholder.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='examiner.Exam'),
        ),
    ]