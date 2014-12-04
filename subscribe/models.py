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

QUESTION_TYPES = (
    ("INT", "Integer"),
    ("TXT", "Text"),
    ("AFD", "Afdeling"),
    ("BOOL", "Ja/Nee"),
    ("CHOICE", "Multiple Choice"),
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

    class Meta:
        ordering = ('-end_registration',)

    def __unicode__(self):
        return self.name

    def subscribed(self):
        return len(Registration.objects.filter(event=self))

    def payed(self):
        return len(Registration.objects.filter(event=self).filter(payed=True))

    def total_payed(self):
        return u"\u20AC %.2f" % (sum([e.price for e in self.registraton_set.filter(payed=True)]) / 100.)

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
        return u"\u20AC %.2f" % (float(self.price) / 100)


class EventQuestion(models.Model):
    event = models.ForeignKey(Event)
    name = models.CharField(max_length=64)
    help = models.CharField(max_length=1024, blank=True)
    question_type = models.CharField(max_length=16, choices=QUESTION_TYPES)
    required = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.question_type)

    def form_id(self):
        return "q%d" % (self.id)

    def delete_event_question(self):
        return u'<a href="/deleteEventQuestion/?optionId=%d">Delete</a>' % (self.id)
    delete_event_question.allow_tags = True


class EventOption(models.Model):
    question = models.ForeignKey('EventQuestion', related_name="options")
    name = models.CharField(max_length=200)
    price = models.IntegerField(help_text="Eurocenten", default=0)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        if self.price != 0:
            return u"%s - \u20AC %.2f" % (self.name, float(self.price) / 100)
        else:
            return u"%s" % (self.name,)

    def price_str(self):
        return u"\u20AC %.2f" % (float(self.price) / 100)

    def delete_event_option(self):
        return u'<a href="/deleteEventOption/?optionId=%d">Delete</a>' % (self.id)
    delete_event_option.allow_tags = True

    def limit_reached(self):
        # Limit is reached when at least one of the registrationlimits has been reached
        for l in self.registrationlimit_set.all():
            if l.is_reached():
                return True
        return False
    limit_reached.boolean = True


class RegistrationLimit(models.Model):
    event = models.ForeignKey(Event)
    options = models.ManyToManyField(EventOption, blank=True)
    limit = models.IntegerField()
    description = models.CharField(max_length=128, help_text="De foutmelding die word weergegeven als de limiet bereikt is (bijv: het hotel is vol).")

    def __unicode__(self):
        return u'Limiet: %d (%s)' % (self.limit, self.description)

    def get_num_registrations(self):
        registrations = Registration.objects.filter(answers__option__in=self.options.all())
        return registrations.count()

    def is_reached(self):
        return self.get_num_registrations() >= self.limit
    is_reached.boolean = True


class Registration(models.Model):
    registration_date = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField(blank=True)
    event = models.ForeignKey(Event)
    price = models.IntegerField(default=0)
    payed = models.BooleanField(default=False)
    status = models.CharField(max_length=64, default="", blank=True)
    trxid = models.CharField(max_length=128, default="", blank=True)

    def calculate_price(self):
        self.price = self.event.price + sum([answer.option.price for answer in self.answers.exclude(option=None)])

    def get_options_name(self):
        name = ''
        for answer in self.answers.all():
            if answer.option is not None:
                name += answer.option.name + ', '
        return name

    def __unicode__(self):
        return u"%s %s - %s - %s" % (self.first_name, self.last_name, self.event, str(self.price))

    def gen_subscription_id(self):
        num_id = str(self.id)
        safe = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        return num_id + "x" + filter(lambda c: c in safe, self.get_options_name())[:15 - len(num_id)]

    def send_confirmation_email(self):
        t = Template(self.event.email_template)
        c = Context({
            "voornaam": self.first_name,
            "achternaam": self.last_name,
            "inschrijf_opties": self.get_options_name(),
        })
        # XXX: Financiele info
        msg = MIMEText(t.render(c).encode('utf-8'), 'plain', 'utf-8')
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


class Answer(models.Model):
    # This should maybe be a "through" model
    registration = models.ForeignKey(Registration, related_name='answers')
    question = models.ForeignKey(EventQuestion)
    int_field = models.IntegerField(default=0, null=True)
    txt_field = models.CharField(max_length=256, blank=True)
    bool_field = models.BooleanField(default=False)
    option = models.ForeignKey(EventOption, default=None, null=True)

    def __unicode__(self):
        return u"%s - %s" % (self.question, self.get_answer())

    def set_answer(self, ans):
        if self.question.question_type == "INT":
            self.int_field = ans
        elif self.question.question_type == "TXT":
            self.txt_field = ans
        elif self.question.question_type == "AFD":
            self.txt_field = ans
        elif self.question.question_type == "BOOL":
            self.bool_field = ans
            if len(self.question.options.all()):
                self.option = self.question.options.all()[0]
        elif self.question.question_type == "CHOICE":
            self.option = ans

    def get_answer(self):
        if self.question.question_type == "INT":
            return self.int_field
        elif self.question.question_type == "TXT":
            return self.txt_field
        elif self.question.question_type == "AFD":
            return self.txt_field
        elif self.question.question_type == "BOOL":
            return self.bool_field
        elif self.question.question_type == "CHOICE":
            return self.option


class IdealIssuer(models.Model):
    issuer_id = models.IntegerField()
    update = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=128)

    def __unicode__(self):
        return self.name

    def safe_id(self):
        return "%04d" % (self.issuer_id)

    class Meta:
        ordering = ['name']
