# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0003_auto_20141201_0124'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='price',
            field=models.IntegerField(default=0, help_text=b'Eurocenten'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='eventoption',
            name='price',
            field=models.IntegerField(default=0, help_text=b'Eurocenten'),
        ),
    ]
