# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def multi_to_question(apps, schema_editor):
    Event = apps.get_model("subscribe", "Event")
    EventOption = apps.get_model("subscribe", "EventOption")
    EventQuestion = apps.get_model("subscribe", "EventQuestion")
    Answer = apps.get_model("subscribe", "Answer")
    Registration = apps.get_model("subscribe", "Registration")

    for e in Event.objects.all():
        for q in e.multi_choice_questions.all():
            # Create eventquestion for this multichoicequestion
            q2 = EventQuestion(name=q.name, question_type="CHOICE", required=q.required, event=e)
            q2.save()
            for a in q.multichoiceanswer_set.all():
                # create eventoption for this multichoiceanswer
                option = EventOption(name=a.name, price=0, event=e, question=q2, active=True)
                option.save()
                # create answer for every option in every registration
                for r in Registration.objects.filter(event=e):
                    if a in r.multi_choice_answers.all():
                        a3 = Answer(question=q2, option=option)
                        a3.save()
                        r.answers.add(a3)
                        r.save()


class Migration(migrations.Migration):

    dependencies = [
        ('subscribe', '0007_add_choice_question'),
    ]

    operations = [
        migrations.RunPython(multi_to_question),
        migrations.RemoveField(
            model_name='multichoiceanswer',
            name='question',
        ),
        migrations.RemoveField(
            model_name='event',
            name='multi_choice_questions',
        ),
        migrations.DeleteModel(
            name='MultiChoiceQuestion',
        ),
        migrations.RemoveField(
            model_name='registration',
            name='multi_choice_answers',
        ),
        migrations.DeleteModel(
            name='MultiChoiceAnswer',
        ),
    ]
