# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def option_to_options(apps, schema_editor):
    Registration = apps.get_model("subscribe", "Registration")
    for reg in Registration.objects.all():
        if reg.event_option is not None:
            reg.event_options.add(reg.event_option)
            reg.event_option = None
            reg.save()


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0004_baseprice'),
    ]

    operations = [
        migrations.RunPython(option_to_options),
        migrations.RemoveField(
            model_name='registration',
            name='event_option',
        ),
    ]
