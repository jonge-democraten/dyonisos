# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0012_eventquestion_order'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='idealissuer',
            name='list_type',
        ),
    ]
