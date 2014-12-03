# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0005_eventoption_to_eventoptions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registration',
            name='payment_check_dates',
        ),
        migrations.DeleteModel(
            name='PaymentCheckDate',
        ),
    ]
