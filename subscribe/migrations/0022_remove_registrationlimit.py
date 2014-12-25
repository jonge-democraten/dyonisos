# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0021_auto_20141208_2334'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registrationlimit',
            name='event',
        ),
        migrations.RemoveField(
            model_name='registrationlimit',
            name='options',
        ),
        migrations.DeleteModel(
            name='RegistrationLimit',
        ),
    ]
