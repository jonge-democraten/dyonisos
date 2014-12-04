# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def calculate_price(apps, schema_editor):
    Registration = apps.get_model('subscribe', 'Registration')
    for r in Registration.objects.all():
        r.price = r.event.price + sum([answer.option.price for answer in r.answers.exclude(option=None)])
        r.save()


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0013_remove_idealissuer_list_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='registration',
            name='price',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
        migrations.RunPython(calculate_price),
    ]
