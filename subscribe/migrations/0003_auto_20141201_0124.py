# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0002_registrationlimit'),
    ]

    operations = [
        migrations.AddField(
            model_name='registration',
            name='event_options',
            field=models.ManyToManyField(related_name=b'event_options', to='subscribe.EventOption'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='answer',
            name='int_field',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='email_template',
            field=models.TextField(help_text=b'Enkele placeholders:\n{{voornaam}}, {{achternaam}}, {{inschrijf_opties}}\n    '),
        ),
        migrations.AlterField(
            model_name='registration',
            name='event_option',
            field=models.ForeignKey(blank=True, to='subscribe.EventOption', null=True),
        ),
    ]
