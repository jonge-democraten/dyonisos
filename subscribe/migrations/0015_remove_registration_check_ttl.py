# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0014_registration_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registration',
            name='check_ttl',
        ),
    ]
