# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0022_remove_registrationlimit'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventquestion',
            name='help',
        ),
    ]
