# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def options_to_question_answer(apps, schema_editor):
    Event = apps.get_model("subscribe", "Event")
    EventQuestion = apps.get_model("subscribe", "EventQuestion")
    for e in Event.objects.all():
        q = [q for q in e.eventquestion_set.all() if q.name == "Opties"]
        if len(q) == 0:
            q = EventQuestion(name="Opties", question_type="CHOICE", required=True, event=e)
            q.save()
        else:
            q = q[0]
        for o in e.eventoption_set.filter(question=None):
            o.question = q
            o.save()

    Registration = apps.get_model("subscribe", "Registration")
    Answer = apps.get_model("subscribe", "Answer")
    for r in Registration.objects.all():
        eq = r.event.eventquestion_set.filter(name="Opties")[0]
        for o in r.event_options.all():
            a = Answer(question=eq, option=o)
            a.save()
            r.answers.add(a)
            r.save()


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0008_remove_multi'),
    ]

    operations = [
        migrations.RunPython(options_to_question_answer),
        migrations.RemoveField(
            model_name='eventoption',
            name='event',
        ),
        migrations.RemoveField(
            model_name='registration',
            name='event_options',
        ),
        migrations.AlterField(
            model_name='event',
            name='email_template',
            field=models.TextField(help_text=b'Enkele placeholders: {{voornaam}}, {{achternaam}}, {{inschrijf_opties}}'),
        ),
    ]
