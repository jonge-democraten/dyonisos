# -*- coding: utf-8 -*-

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

import datetime
import logging
from lib import mollie

from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.views.generic.list import ListView
from django.utils.html import escape
from django.utils.safestring import mark_safe

from subscribe.models import Event, EventQuestion
from subscribe.forms import Registration, SubscribeForm, fill_subscription

from django.conf import settings


def _safe_string(s, max_len=32):
    safe = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ")
    return filter(lambda c: c in safe, s)[:max_len]


def event_message(request, event, message):
    c = {"event": event, "request": request, "message": message}
    return render_to_response("subscribe/event_message.html", c)


def register(request, slug):
    logger = logging.getLogger(__name__)

    logger.info('views::register() - start')
    event = get_object_or_404(Event, slug=slug)
    now = datetime.datetime.now()
    if not request.user.is_staff:
        if event.start_registration > now or event.end_registration < now:
            return event_message(request, event, _("Inschrijving gesloten."))
        if event.is_full():
            return event_message(request, event, _("Helaas is het maximum aantal inschrijvingen bereikt."))
    # SubscribeForm = SubscribeFormBuilder(event)
    if request.method == "POST":
        logger.info('views::register() - form POST')
        form = SubscribeForm(event, request.POST)
        valid = form.is_valid()
        if valid and 'registration_preview' not in request.POST:
            form.confirm_page()
            c = {"event": event, "request": request, "form": form}
            c['user_is_staff'] = request.user.is_staff
            c.update(csrf(request))
            return render_to_response("subscribe/form.html", c)
        elif valid:
            if 'testsubmit' in request.POST:
                subscription = fill_subscription(form, event)
                msg = subscription.send_confirmation_email()
                subscription.delete()
                msg = '<br/>'.join(escape(msg).split('\n'))
                return event_message(request, event, mark_safe(u"De volgende email is verstuurd:<br/><br/>{}".format(msg)))
            # Store the data
            subscription = fill_subscription(form, event)
            if subscription in event.get_registrations_over_limit():
                subscription.delete()
                if event.is_full():
                    error_str = "De inschrijving kan niet worden voltooid, omdat het maximum aantal inschrijvingen is bereikt."
                else:
                    error_str = "De inschrijving kan niet worden voltooid, omdat een van de gekozen opties het maximum aantal inschrijvingen heeft bereikt."
                logger.error(error_str)
                return event_message(request, event, _(error_str))
            if not subscription:
                # Error Filling subscription
                error_str = "Error in saving form."
                logger.error(error_str)
                return HttpResponse(_(error_str))
            if subscription.price <= 0:
                subscription.payed = True
                subscription.send_confirmation_email()
                subscription.save()
                logger.info('views::register() - registered for a free event.')
                return event_message(request, event, _("Inschrijving geslaagd. Ter bevestiging is een e-mail verstuurd."))

            # You need to pay
            response = mollie.fetch(
                settings.MOLLIE['partner_id'],          # Partner id
                subscription.price,                     # Amount
                form.cleaned_data["issuer"].safe_id(),  # Bank ID
                subscription.event.name,                # Description
                settings.MOLLIE['report_url'],          # Report url
                settings.MOLLIE['return_url'],          # Return url
                settings.MOLLIE['profile_key'],         # Return url
            )

            err = mollie.get_error(response)
            if err:
                error_str = "views::register() - Technische fout, probeer later opnieuw." + "\n\n%d: %s" % (err[0], err[1])
                logger.error(error_str)
                return event_message(request, event, _(error_str))

            subscription.trxid = response.order.transaction_id
            subscription.save()

            logger.info(response.order.URL)
            return HttpResponseRedirect(str(response.order.URL))

    else:
        form = SubscribeForm(event)
    c = {"event": event, "request": request, "form": form, }
    c['user_is_staff'] = request.user.is_staff
    c.update(csrf(request))
    return render_to_response("subscribe/form.html", c)


# called when the user returns from iDeal, is set as MERCHANTRETURNURL.
def return_page(request):
    transaction_id = request.GET['transaction_id']
    logger = logging.getLogger(__name__)
    logger.info('views::return_page() - transaction id: ' + str(transaction_id))
    try:
        subscription = Registration.objects.get(trxid=transaction_id)
    except:
        return HttpResponse(_("iDEAL error (onbekende inschrijving): Neem contact op met ict@jongedemocraten.nl. Controleer of uw betaling is afgeschreven alvorens de betaling opnieuw uit te voeren."))

    logger.info('views::return_page() - transaction in database: ' + subscription.status)
    logger.info('views::return_page() - transaction payed: ' + str(subscription.payed))

    if subscription.status == "":
        check(request)
        subscription = Registration.objects.get(trxid=transaction_id)

    if subscription.payed and subscription.status == "Success":
        return event_message(request, subscription.event, _("Betaling geslaagd. Ter bevestiging is een e-mail verstuurd."))
    elif subscription.status == "Cancelled":
        return event_message(request, subscription.event, _("Je betaling is geannuleerd."))
    elif subscription.status == "Failure":
        return event_message(request, subscription.event, _("Je betaling is om onbekende reden niet gelukt. Er is geen geld afgeschreven. Neem contact op met ict@jongedemocraten.nl of probeer het nogmaals."))
    elif subscription.status == "Expired":
        return event_message(request, subscription.event, _("Je betaling is geannuleerd."))
    elif subscription.status == "Open":
        return event_message(request, subscription.event, _("Je betaling staat geregistreerd in ons systeem, maar wordt nog verwerkt door onze bank. Als je binnen een uur geen bevestigingsmail ontvangt, is er mogelijk iets fout gegaan met de betaling. Neem in dat geval contact op met ict@jongedemocraten.nl."))
    else:
        return event_message(request, subscription.event, _("Er is een fout opgetreden bij het verwerken van je iDEAL transactie. Neem contact op met ict@jongedemocraten.nl of probeer het later nogmaals. Controleer of je betaling is afgeschreven alvorens de betaling opnieuw uit te voeren."))


def check(request):
    transaction_id = request.GET['transaction_id']

    logger = logging.getLogger(__name__)
    logger.info('views::check() - transaction id: ' + str(transaction_id))

    response = mollie.check(settings.MOLLIE['partner_id'], transaction_id)
    logger.info('views::check() - status: ' + str(response.order.status))

    try:
        subscription = Registration.objects.get(trxid=transaction_id)
    except:
        logger.error("views::check() - cannot find subscription with transaction id: " + str(transaction_id))
        return HttpResponse(_("NOT OK"))

    if response.order.status == "CheckedBefore":
        return HttpResponse(_("OK"))
    elif response.order.payed and response.order.status == "Success":  # Mollie gives payed=true and status=Success only once
        subscription.payed = True
        subscription.status = "Success"
        subscription.save()
        logger.info('views::check() - subscription saved to database')
        subscription.send_confirmation_email()
        logger.info('views::check() - payed, saved and mail sent')
        return HttpResponse(_("OK"))
    else:
        subscription.payed = False
        subscription.status = response.order.status
        subscription.save()

    return HttpResponse(_("OK"))


@login_required
def delete_event_question(request):
    questionId = request.GET['questionId']
    warning = int(request.GET['warning'])

    if warning == 0:
        eventQuestion = EventQuestion.objects.get(pk=questionId)
        eventQuestion.delete()
        return HttpResponse(_(u'Vraag verwijderd. <br /> <a href="/admin/">Terug naar admin.</a>'))
    else:
        return HttpResponse(_("""Weet je zeker dat je deze vraag wilt verwijderen? <br />
                                 <a href="/deleteEventQuestion/?questionId=%d&warning=%d">Ja</a>
                                 <a href="/admin/">Nee</a>""" % (int(questionId), 0)))


class HomeView(ListView):
    model = Event
    queryset = Event.objects.order_by('-end_registration', '-start_registration')
    template_name = "subscribe/index.html"
    context_object_name = "events"

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            now = datetime.datetime.now()
            self.queryset = self.queryset.filter(start_registration__lte=now, end_registration__gte=now)
        return super(HomeView, self).get(self, request, *args, **kwargs)
