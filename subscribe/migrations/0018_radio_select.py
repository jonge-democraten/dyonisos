# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0017_add_text_element'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventquestion',
            name='radio',
            field=models.BooleanField(default=False, help_text=b'Voor multiple-choice: geen dropdown maar radio buttons'),
            preserve_default=True,
        ),
    ]
