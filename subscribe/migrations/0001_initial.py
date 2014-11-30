# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('int_field', models.IntegerField(default=0)),
                ('txt_field', models.CharField(max_length=256, blank=True)),
                ('bool_field', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField()),
                ('start_registration', models.DateTimeField()),
                ('end_registration', models.DateTimeField()),
                ('description', models.TextField()),
                ('contact_email', models.EmailField(max_length=75)),
                ('email_template', models.TextField(help_text=b'Enkele placeholders:\n{{voornaam}}, {{achternaam}}, {{inschrijf_optie}}\n    ')),
            ],
            options={
                'ordering': ('-end_registration',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('price', models.IntegerField(help_text=b'Eurocenten')),
                ('active', models.BooleanField(default=True)),
                ('event', models.ForeignKey(to='subscribe.Event')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('help', models.CharField(max_length=1024, blank=True)),
                ('question_type', models.CharField(max_length=16, choices=[(b'INT', b'Integer'), (b'TXT', b'Text'), (b'AFD', b'Afdeling'), (b'BOOL', b'Ja/Nee')])),
                ('required', models.BooleanField(default=False)),
                ('event', models.ForeignKey(to='subscribe.Event')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IdealIssuer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('issuer_id', models.IntegerField()),
                ('update', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=128)),
                ('list_type', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultiChoiceAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'', max_length=256)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultiChoiceQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'', max_length=256)),
                ('required', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PaymentCheckDate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Registration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('registration_date', models.DateTimeField(auto_now_add=True)),
                ('first_name', models.CharField(max_length=64)),
                ('last_name', models.CharField(max_length=64)),
                ('email', models.EmailField(max_length=75, blank=True)),
                ('payed', models.BooleanField(default=False)),
                ('status', models.CharField(default=b'', max_length=64, blank=True)),
                ('trxid', models.CharField(default=b'', max_length=128, blank=True)),
                ('check_ttl', models.IntegerField(default=10)),
                ('answers', models.ManyToManyField(to='subscribe.Answer', null=True)),
                ('event', models.ForeignKey(to='subscribe.Event')),
                ('event_option', models.ForeignKey(to='subscribe.EventOption')),
                ('multi_choice_answers', models.ManyToManyField(to='subscribe.MultiChoiceAnswer', null=True)),
                ('payment_check_dates', models.ManyToManyField(to='subscribe.PaymentCheckDate')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='multichoiceanswer',
            name='question',
            field=models.ForeignKey(default=b'', blank=True, to='subscribe.MultiChoiceQuestion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='multi_choice_questions',
            field=models.ManyToManyField(default=b'', to='subscribe.MultiChoiceQuestion', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(to='subscribe.EventQuestion'),
            preserve_default=True,
        ),
    ]
