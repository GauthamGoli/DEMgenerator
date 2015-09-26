# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gmap', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sublineoi',
            name='name',
            field=models.CharField(default='a', max_length=50),
            preserve_default=False,
        ),
    ]
