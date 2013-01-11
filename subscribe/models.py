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

from lib.ideal import *

import datetime
import smtplib
from email.mime.text import MIMEText

AFDELINGEN = (
    ("AMS", "Amsterdam"),
    ("AN", "Arnhem-Nijmegen"),
    ("BB", "Brabant"),
    ("FR", "Friesland"),
    ("GR", "Groningen"),
    ("LH", "Leiden-Haaglanden"),
    ("MS", "Maastricht"),
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
    
    def update_all_event_transaction_statuses(self):
        return u'<a href="/updateEventTransactionStatuses/?eventId=%d">Update all transactions</a>' % (self.id)
            
    update_all_event_transaction_statuses.allow_tags = True        

class EventOption(models.Model):
    name = models.CharField(max_length=200)
    price = models.IntegerField(help_text="Eurocenten")
    event = models.ForeignKey(Event)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return u"%s - \u20AC %.2f" % (self.name, float(self.price)/100)

    def price_str(self):
        return u"\u20AC %.2f" % (float(self.price)/100)

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

class Registration(models.Model):
    registration_date = models.DateTimeField(auto_now_add=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField(blank=True)
    event_option = models.ForeignKey(EventOption)
    event = models.ForeignKey(Event)
    answers = models.ManyToManyField(Answer, null=True)
    payed = models.BooleanField(default=False)
    trxid = models.CharField(max_length=128, default="", blank=True)
    check_ttl = models.IntegerField(default=5)
    

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
        s = smtplib.SMTP("localhost:587")
        s.sendmail(self.event.contact_email, [self.email], msg.as_string().encode('ascii','replace'))
        s.quit()

    def check_payment_status(self):
        if self.payed:
            return True # Has payed
        if self.check_ttl <= 0:
            return False # Give up and don't check again.
        if not self.trxid:
            return None # trxid not set, can't check
        else:
            # check payment with ideal provider
            oIDC = iDEALConnector()
            req_status = oIDC.RequestTransactionStatus(self.trxid)
            if not req_status.IsResponseError():
                if req_status.getStatus() == IDEAL_TX_STATUS_SUCCESS:
                    self.payed = True
                    self.send_confirmation_email()
                    self.save()
                    return True
                elif req_status.getStatus() == IDEAL_TX_STATUS_CANCELLED:
                    self.check_ttl = 0 # Don't check again
                    self.save()
                    return False
                else:
                    self.check_ttl -= 1 # Check later
                    self.save()
                    return None
            else:
                print 'models::check_payment_status() - ERROR RequestTransactionStatus: ' + req_status.getErrorMessage()
                self.check_ttl -= 1
                self.save()
                return None                
                        

    def check_link(self):
        return u'<a href="/check/?ec=%dxcheck">Check</a>' % (self.id)
    
    def update_transaction_status(self):
        return u'<a href="/updateTransactionStatus/?ec=%d">Update Transaction Status</a>' % (self.id)
    
    check_link.allow_tags = True
    update_transaction_status.allow_tags = True


class IdealIssuer(models.Model):
    issuer_id = models.IntegerField()
    update = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=128)
    list_type = models.CharField(max_length=128)
    
    def __unicode__(self):
        return self.name

    def safe_id(self):
        return "%04d" % (self.issuer_id)



