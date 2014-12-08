# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0020_eventoption_limit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventquestion',
            name='order',
            field=models.IntegerField(default=0, help_text=b'Bepaalt volgorde op formulier; gebruik order<0 voor elementen vooraf aan voornaam, achternaam en email'),
        ),
        migrations.AlterField(
            model_name='eventquestion',
            name='radio',
            field=models.BooleanField(default=False, help_text=b'Voor multiple-choice/afdeling: geen dropdown maar radio buttons'),
        ),
        migrations.AlterField(
            model_name='eventquestion',
            name='required',
            field=models.BooleanField(default=False, help_text=b'Bij Ja/Nee: verplicht aanvinken; bij andere: verplicht invullen'),
        ),
        migrations.AlterField(
            model_name='eventquestion',
            name='text',
            field=models.TextField(default=b'', help_text=b'Voor "HTML Text"; geldige HTML tags: a, b/strong, code, em/i, h3, img, ul, ol, li, p, br; Geldige HTML attributen: class, style, a.href, a.target, img.src, img.alt', blank=True),
        ),
    ]
