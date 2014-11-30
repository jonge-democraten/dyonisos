# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistrationLimit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('limit', models.IntegerField()),
                ('description', models.CharField(help_text=b'De foutmelding die word weergegeven als de limiet bereikt is (bijv: het hotel is vol).', max_length=128)),
                ('event', models.ForeignKey(blank=True, to='subscribe.Event', null=True)),
                ('options', models.ManyToManyField(to='subscribe.EventOption', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
