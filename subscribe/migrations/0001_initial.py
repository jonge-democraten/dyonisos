# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('int_field', models.IntegerField(default=0, null=True)),
                ('txt_field', models.CharField(max_length=256, blank=True)),
                ('bool_field', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField()),
                ('start_registration', models.DateTimeField()),
                ('end_registration', models.DateTimeField()),
                ('description', models.TextField()),
                ('contact_email', models.EmailField(max_length=254)),
                ('email_template', models.TextField(help_text='Enkele placeholders: {{voornaam}}, {{achternaam}}, {{inschrijf_opties}}')),
                ('price', models.IntegerField(help_text='Eurocenten', default=0)),
                ('max_registrations', models.IntegerField(help_text='Als groter dan 0, bepaalt maximaal aantal inschrijvingen', default=0)),
            ],
            options={
                'ordering': ('-end_registration',),
            },
        ),
        migrations.CreateModel(
            name='EventOption',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=200)),
                ('price', models.IntegerField(help_text='Eurocenten', default=0)),
                ('active', models.BooleanField(default=True)),
                ('order', models.IntegerField(default=0)),
                ('limit', models.IntegerField(help_text='Aantal beschikbare plekken (0 = geen limiet)', default=0)),
            ],
        ),
        migrations.CreateModel(
            name='EventQuestion',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=64)),
                ('question_type', models.CharField(max_length=16, choices=[('INT', 'Integer'), ('TXT', 'Text Input'), ('AFD', 'Afdeling'), ('BOOL', 'Ja/Nee'), ('CHOICE', 'Multiple Choice'), ('TEXT', 'HTML Text')])),
                ('required', models.BooleanField(help_text='Bij Ja/Nee: verplicht aanvinken; bij andere: verplicht invullen', default=False)),
                ('radio', models.BooleanField(help_text='Voor multiple-choice/afdeling: geen dropdown maar radio buttons', default=False)),
                ('order', models.IntegerField(help_text='Bepaalt volgorde op formulier; gebruik order<0 voor elementen vooraf aan voornaam, achternaam en email', default=0)),
                ('text', models.TextField(help_text='Voor "HTML Text"; geldige HTML tags: a, b/strong, code, em/i, h3, img, ul, ol, li, p, br; Geldige HTML attributen: class, style, a.href, a.target, img.src, img.alt', default='', blank=True)),
                ('event', models.ForeignKey(to='subscribe.Event')),
            ],
        ),
        migrations.CreateModel(
            name='IdealIssuer',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('issuer_id', models.IntegerField()),
                ('update', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Registration',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('registration_date', models.DateTimeField(auto_now_add=True)),
                ('first_name', models.CharField(max_length=64)),
                ('last_name', models.CharField(max_length=64)),
                ('email', models.EmailField(max_length=254, blank=True)),
                ('price', models.IntegerField(default=0)),
                ('payed', models.BooleanField(default=False)),
                ('status', models.CharField(max_length=64, default='', blank=True)),
                ('trxid', models.CharField(max_length=128, default='', blank=True)),
                ('event', models.ForeignKey(related_name='registrations', to='subscribe.Event')),
            ],
        ),
        migrations.AddField(
            model_name='eventoption',
            name='question',
            field=models.ForeignKey(related_name='options', to='subscribe.EventQuestion'),
        ),
        migrations.AddField(
            model_name='answer',
            name='option',
            field=models.ForeignKey(default=None, to='subscribe.EventOption', null=True),
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(to='subscribe.EventQuestion'),
        ),
        migrations.AddField(
            model_name='answer',
            name='registration',
            field=models.ForeignKey(related_name='answers', to='subscribe.Registration'),
        ),
    ]
