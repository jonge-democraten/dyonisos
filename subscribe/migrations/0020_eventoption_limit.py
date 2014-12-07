# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0019_eventoption_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventoption',
            name='limit',
            field=models.IntegerField(default=0, help_text=b'Aantal beschikbare plekken (0 = geen limiet)'),
            preserve_default=True,
        ),
    ]
