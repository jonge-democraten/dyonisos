# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0011_fix_aggregation'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventquestion',
            name='order',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
    ]
