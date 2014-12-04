# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0006_remove_paymentcheckdate'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='option',
            field=models.ForeignKey(default=None, to='subscribe.EventOption', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='eventquestion',
            name='question_type',
            field=models.CharField(max_length=16, choices=[(b'INT', b'Integer'), (b'TXT', b'Text'), (b'AFD', b'Afdeling'), (b'BOOL', b'Ja/Nee'), (b'CHOICE', b'Multiple Choice')]),
        ),
        migrations.AddField(
            model_name='eventoption',
            name='question',
            field=models.ForeignKey(related_name=b'options', default=None, to='subscribe.EventQuestion', null=True),
            preserve_default=True,
        ),
    ]
