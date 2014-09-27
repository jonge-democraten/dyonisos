###############################################################################
# Copyright (c) 2011, Floor Terra <floort@gmail.com>
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
############################################################################### 

from django.db import models
from django.template import Context, Template

import datetime
import smtplib
import logging
from email.mime.text import MIMEText

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
)


class MultiChoiceQuestion(models.Model):
    name = models.CharField(max_length=256, blank=False, default='')
    required = models.BooleanField(default=False)
    
    def __unicode__(self):
        return self.name


class MultiChoiceAnswer(models.Model):
    name = models.CharField(max_length=256, blank=False, default='')
    question = models.ForeignKey(MultiChoiceQuestion, blank=True, default='')
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Event(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField()
    start_registration = models.DateTimeField()
    end_registration = models.DateTimeField()
    description = models.TextField()
    contact_email = models.EmailField()
    email_template = models.TextField(help_text="""Enkele placeholders:
{{voornaam}}, {{achternaam}}, {{inschrijf_optie}}
    """)
    multi_choice_questions = models.ManyToManyField(MultiChoiceQuestion, blank=True, default='')
    
    class Meta:
        ordering = ('-end_registration',)
    
    def __unicode__(self):
        return self.name
    
    def subscribed(self):
        return len(Registration.objects.filter(event=self))
    
    def payed(self):
        return len(Registration.objects.filter(event=self).filter(payed=True))

    def total_payed(self):
        return u"\u20AC %.2f" % (sum([e.event_option.price for e in Registration.objects.filter(event=self).filter(payed=True)])/100.)
    
    def form_link(self):
        return "<a href=\"https://events.jongedemocraten.nl/inschrijven/%s/\">Inschrijven</a>" % (self.slug)
    form_link.allow_tags = True
    
    def all_free(self):
        """Are all event options free?"""
        if self.eventoption_set.filter(price__gt=0):
            return False
        return True

    def active(self):
        now = datetime.datetime.now()
        if self.start_registration > now or self.end_registration < now:
            return False
        return True
    #active.boolean = True        


class EventOption(models.Model):
    name = models.CharField(max_length=200)
    price = models.IntegerField(help_text="Eurocenten")
    event = models.ForeignKey(Event)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return u"%s - \u20AC %.2f" % (self.name, float(self.price)/100)

    def price_str(self):
        return u"\u20AC %.2f" % (float(self.price)/100)
    
    def delete_event_option(self):
        return u'<a href="/deleteEventOption/?optionId=%d">Delete</a>' % (self.id)
    delete_event_option.allow_tags = True


class EventQuestion(models.Model):
    name = models.CharField(max_length=64)
    help = models.CharField(max_length=1024, blank=True)
    question_type = models.CharField(max_length=16, choices=QUESTION_TYPES)
    required = models.BooleanField(default=False)
    event = models.ForeignKey(Event)
    
    def __unicode__(self):
        return "%s (%s)" % (self.name, self.question_type)
    def form_id(self):
        return "q%d" % (self.id)
    def delete_event_question(self):
        return u'<a href="/deleteEventQuestion/?optionId=%d">Delete</a>' % (self.id)
    delete_event_question.allow_tags = True
    

class Answer(models.Model):
    question = models.ForeignKey(EventQuestion)
    int_field = models.IntegerField(default=0)
    txt_field = models.CharField(max_length=256, blank=True)
    bool_field = models.BooleanField(default=False)
    
    def __unicode__(self):
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
    
    def get_answer(self):
        if self.question.question_type == "INT":
            return self.int_field
        elif self.question.question_type == "TXT":
            return self.txt_field
        elif self.question.question_type == "AFD":
            return self.txt_field
        elif self.question.question_type == "BOOL":
            return self.bool_field


class PaymentCheckDate(models.Model):
    date = models.DateTimeField(auto_now_add=True)

    
class Registration(models.Model):
    registration_date = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField(blank=True)
    event_option = models.ForeignKey(EventOption)
    event = models.ForeignKey(Event)
    answers = models.ManyToManyField(Answer, null=True)
    multi_choice_answers = models.ManyToManyField(MultiChoiceAnswer, null=True)
    payed = models.BooleanField(default=False)
    status = models.CharField(max_length=64, default="", blank=True)
    trxid = models.CharField(max_length=128, default="", blank=True)
    check_ttl = models.IntegerField(default=10)
    payment_check_dates = models.ManyToManyField(PaymentCheckDate)
    
    def __unicode__(self):
        return "%s %s - %s - %s" % (self.first_name, self.last_name, self.event, self.event_option.price_str())

    def gen_subscription_id(self):
        num_id = str(self.id)
        safe = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        return num_id+"x"+filter(lambda c: c in safe, self.event_option.name)[:15-len(num_id)]

    def send_confirmation_email(self):
        t = Template(self.event.email_template)
        c = Context({
            "voornaam": self.first_name,
            "achternaam": self.last_name,
            "inschrijf_optie": self.event_option,
        })
        #XXX: Financiele info
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
            logger = logging.getLogger(__name__)
            logger.error("Could not send welcome mail to %s" % (self.email))


class IdealIssuer(models.Model):
    issuer_id = models.IntegerField()
    update = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=128)
    list_type = models.CharField(max_length=128)
    
    def __unicode__(self):
        return self.name
    
    def safe_id(self):
        return "%04d" % (self.issuer_id)

    class Meta:
        ordering = ['name']

