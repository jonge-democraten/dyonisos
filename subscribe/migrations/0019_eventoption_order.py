# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0018_radio_select'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventoption',
            name='order',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
    ]
