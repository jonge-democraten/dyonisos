# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0010_manytomany_to_fk'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventoption',
            name='question',
            field=models.ForeignKey(related_name=b'options', to='subscribe.EventQuestion'),
        ),
        migrations.AlterField(
            model_name='registrationlimit',
            name='event',
            field=models.ForeignKey(to='subscribe.Event'),
        ),
    ]
