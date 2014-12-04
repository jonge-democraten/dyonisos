# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def convert(apps, schema_editor):
    Answer = apps.get_model('subscribe', 'Answer')
    for a in Answer.objects.all():
        regs = a.registration_set.all()
        if len(regs) == 0:
            a.delete()
        else:
            a.registration2 = regs[0]
            a.save()
            for r in regs[1:]:
                a.registration2 = r
                a.pk = None
                a.save()

    assert len(Answer.objects.filter(registration2=None)) == 0


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0009_options_to_question_answer'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='registration2',
            field=models.ForeignKey(default=None, to='subscribe.Registration', null=True),
            preserve_default=False,
        ),
        migrations.RunPython(convert),
        migrations.RemoveField(
            model_name='registration',
            name='answers',
        ),
        migrations.RenameField(
            model_name='answer',
            old_name='registration2',
            new_name='registration',
        ),
        migrations.AlterField(
            model_name='answer',
            name='registration',
            field=models.ForeignKey(related_name=b'answers', to='subscribe.Registration'),
        ),
    ]
