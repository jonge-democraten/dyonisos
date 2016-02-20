# -*- coding: utf-8 -*-

# Copyright (c) 2011,2014 Floor Terra <floort@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


from django.db import models
from django.template import Context, Template

import datetime
import smtplib
import logging
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

AFDELINGEN = (
    ("AMS", "Amsterdam"),
    ("AN", "Arnhem-Nijmegen"),
    ("BB", "Brabant"),
    ("FR", "Friesland"),
    ("GR", "Groningen"),
    ("LH", "Leiden-Haaglanden"),
    ("MS", "Limburg"),
    ("RD", "Rotterdam"),
    ("TW", "Twente"),
    ("UT", "Utrecht"),
    ("INT", "Internationaal"),
)


def afdeling_text(afd):
    for key, value in AFDELINGEN:
        if key == afd:
            return value
    return None


QUESTION_TYPES = (
    ("INT", "Integer"),
    ("TXT", "Text Input"),
    ("AFD", "Afdeling"),
    ("BOOL", "Ja/Nee"),
    ("CHOICE", "Multiple Choice"),
    ("TEXT", "HTML Text"),
)


class Event(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField()
    start_registration = models.DateTimeField()
    end_registration = models.DateTimeField()
    description = models.TextField()
    contact_email = models.EmailField()
    email_template = models.TextField(help_text="Enkele placeholders: {{voornaam}}, {{achternaam}}, {{inschrijf_opties}}")
    price = models.IntegerField(help_text="Eurocenten", default=0)
    max_registrations = models.IntegerField(default=0, help_text="Als groter dan 0, bepaalt maximaal aantal inschrijvingen")

    class Meta:
        ordering = ('-end_registration',)

    def __str__(self):
        return self.name

    def subscribed(self):
        return len(Registration.objects.filter(event=self))

    def paid(self):
        return len(Registration.objects.filter(event=self).filter(paid=True))

    def total_paid(self):
        return "\u20AC %.2f" % (sum([e.price for e in self.registrations.filter(paid=True)]) / 100.)

    def form_link(self):
        return "<a href=\"https://events.jongedemocraten.nl/inschrijven/%s/\">Inschrijven</a>" % (self.slug)
    form_link.allow_tags = True

    def all_free(self):
        """Are all event options free?"""
        if self.price != 0:
            return False
        if len(EventOption.objects.filter(price__gt=0).filter(question__event=self)):
            return False
        return True

    def active(self):
        now = datetime.datetime.now()
        if self.start_registration > now or self.end_registration < now:
            return False
        return True
    # active.boolean = True

    def price_str(self):
        return "\u20AC %.2f" % (float(self.price) / 100)

    def is_full(self):
        if self.max_registrations <= 0:
            return False
        return self.registrations.count() >= self.max_registrations
    is_full.boolean = True

    def get_registrations_over_limit(self):
        results = []
        if self.max_registrations > 0:
            results += self.registrations.order_by('pk')[int(self.max_registrations):]
        for question in self.eventquestion_set.all():
            for option in question.options.all():
                results += option.get_registrations_over_limit()
        return results


class EventQuestion(models.Model):
    event = models.ForeignKey(Event)
    name = models.CharField(max_length=64)
    question_type = models.CharField(max_length=16, choices=QUESTION_TYPES)
    required = models.BooleanField(default=False, help_text='Bij Ja/Nee: verplicht aanvinken; bij andere: verplicht invullen')
    radio = models.BooleanField(default=False, help_text='Voor multiple-choice/afdeling: geen dropdown maar radio buttons')
    order = models.IntegerField(default=0, help_text='Bepaalt volgorde op formulier; gebruik order<0 voor elementen vooraf aan voornaam, achternaam en email')
    text = models.TextField(blank=True, default='', help_text='Voor "HTML Text"; geldige HTML tags: a, b/strong, code, em/i, h3, img, ul, ol, li, p, br; Geldige HTML attributen: class, style, a.href, a.target, img.src, img.alt')

    def __str__(self):
        return "%s (%s)" % (self.name, self.question_type)

    def form_id(self):
        return "q%d" % (self.id)

    def delete_event_question(self):
        return '<a href="/deleteEventQuestion/?optionId=%d">Delete</a>' % (self.id)
    delete_event_question.allow_tags = True


class EventOption(models.Model):
    question = models.ForeignKey('EventQuestion', related_name="options")
    name = models.CharField(max_length=200)
    price = models.IntegerField(help_text="Eurocenten", default=0)
    active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    limit = models.IntegerField(default=0, help_text="Aantal beschikbare plekken (0 = geen limiet)")

    def __str__(self):
        if self.price < 0:
            return "%s: \u20AC %.2f korting" % (self.name, float(-self.price) / 100)
        if self.price > 0:
            return "%s: \u20AC %.2f" % (self.name, float(self.price) / 100)
        else:
            return "%s" % (self.name,)

    def price_str(self):
        return "\u20AC %.2f" % (float(self.price) / 100)

    def delete_event_option(self):
        return '<a href="/deleteEventOption/?optionId=%d">Delete</a>' % (self.id)
    delete_event_option.allow_tags = True

    def get_related_registrations(self):
        return Registration.objects.filter(answers__option=self).order_by('pk')

    def num_registrations(self):
        registrations = self.get_related_registrations()
        return registrations.count()

    def is_full(self):
        if self.limit <= 0:
            return False
        return self.num_registrations() >= self.limit
    is_full.boolean = True

    def limit_str(self):
        if self.limit <= 0:
            return "-"
        return "{}/{}".format(self.num_registrations(), self.limit)
    limit_str.short_description = "Limit usage"

    def get_registrations_over_limit(self):
        if self.limit <= 0:
            return []
        registrations = self.get_related_registrations()
        return registrations[int(self.limit):]

    def limit_reached(self):
        return self.is_full()
    limit_reached.boolean = True


class Registration(models.Model):
    registration_date = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField(blank=True)
    event = models.ForeignKey(Event, related_name='registrations')
    price = models.IntegerField(default=0)
    paid = models.BooleanField(default=False)
    status = models.CharField(max_length=64, default="", blank=True)
    trxid = models.CharField(max_length=128, default="", blank=True)

    def calculate_price(self):
        self.price = self.event.price + sum([answer.option.price for answer in self.answers.exclude(option=None)])

    def get_options_text(self):
        results = []
        added_default_fields = False
        answers = {a.question: a.get_answer() for a in self.answers.all()}
        for question in self.event.eventquestion_set.order_by('order'):
            if question.order >= 0 and not added_default_fields:
                results += ["Voornaam: {}".format(self.first_name)]
                results += ["Achternaam: {}".format(self.last_name)]
                results += ["Email: {}".format(self.email)]
                added_default_fields = True
            if question in answers:
                results += ["{}: {}".format(question.name, answers[question])]
        if not added_default_fields:
            results += ["Voornaam: {}".format(self.first_name)]
            results += ["Achternaam: {}".format(self.last_name)]
            results += ["Email: {}".format(self.email)]
        return '\n'.join(results)

    def __str__(self):
        return "%s %s - %s - %s" % (self.first_name, self.last_name, self.event, str(self.price))

    def gen_subscription_id(self):
        num_id = str(self.id)
        safe = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        return num_id + "x" + filter(lambda c: c in safe, self.get_options_name())[:15 - len(num_id)]

    def send_confirmation_email(self):
        t = Template(self.event.email_template)
        c = Context({
            "voornaam": self.first_name,
            "achternaam": self.last_name,
            "inschrijf_opties": self.get_options_text(),
        })
        # XXX: Financiele info
        rendered_mail = t.render(c).encode('utf-8')
        msg = MIMEText(rendered_mail, 'plain', 'utf-8')
        msg.set_charset("utf-8")
        msg["Subject"] = "Inschrijfbevestiging: %s" % (self.event.name)
        msg["From"] = self.event.contact_email
        msg["To"] = self.email
        # Send msg
        try:
            s = smtplib.SMTP("localhost:587")
            s.sendmail(self.event.contact_email, [self.email], msg.as_string())
            s.quit()
        except:
            logger.error("Could not send welcome mail to %s" % (self.email))
        return rendered_mail


class Answer(models.Model):
    # This should maybe be a "through" model
    registration = models.ForeignKey(Registration, related_name='answers')
    question = models.ForeignKey(EventQuestion)
    int_field = models.IntegerField(default=0, null=True)
    txt_field = models.CharField(max_length=256, blank=True)
    bool_field = models.BooleanField(default=False)
    option = models.ForeignKey(EventOption, default=None, null=True)

    def __str__(self):
        return "%s - %s" % (self.question, self.get_answer())

    def set_answer(self, ans):
        if self.question.question_type == "INT":
            self.int_field = ans
        elif self.question.question_type == "TXT":
            self.txt_field = ans
        elif self.question.question_type == "AFD":
            self.txt_field = ans
        elif self.question.question_type == "BOOL":
            self.bool_field = ans
            if self.bool_field and len(self.question.options.all()):
                self.option = self.question.options.all()[0]
            else:
                self.option = None
        elif self.question.question_type == "CHOICE":
            self.option = ans

    def get_answer(self):
        if self.question.question_type == "INT":
            return self.int_field
        elif self.question.question_type == "TXT":
            return self.txt_field
        elif self.question.question_type == "AFD":
            return afdeling_text(self.txt_field)
        elif self.question.question_type == "BOOL":
            if self.option is not None:
                return self.option
            else:
                return self.bool_field and 'Ja' or 'Nee'
        elif self.question.question_type == "CHOICE":
            return self.option
