# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-12-20 13:45
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('examiner', '0009_auto_20181220_1443'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ScrapedPdfUrl',
            new_name='PdfUrl',
        ),
    ]