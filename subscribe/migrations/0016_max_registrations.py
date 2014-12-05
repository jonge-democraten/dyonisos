# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0015_remove_registration_check_ttl'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='max_registrations',
            field=models.IntegerField(default=0, help_text=b'Als groter dan 0, bepaalt maximaal aantal inschrijvingen'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='registration',
            name='event',
            field=models.ForeignKey(related_name=b'registrations', to='subscribe.Event'),
        ),
    ]
