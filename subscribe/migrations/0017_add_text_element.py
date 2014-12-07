# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0016_max_registrations'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventquestion',
            name='text',
            field=models.TextField(default=b'', help_text=b'Geldige HTML tags: a, b/strong, code, em/i, h3, img, ul, ol, li, p, br; Geldige HTML attributen: class, style, a.href, a.target, img.src, img.alt', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='eventquestion',
            name='question_type',
            field=models.CharField(max_length=16, choices=[(b'INT', b'Integer'), (b'TXT', b'Text Input'), (b'AFD', b'Afdeling'), (b'BOOL', b'Ja/Nee'), (b'CHOICE', b'Multiple Choice'), (b'TEXT', b'HTML Text')]),
        ),
    ]
