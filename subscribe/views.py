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

import datetime
import logging
from lib import mollie

from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.db.transaction import commit_on_success

from subscribe.models import Event, EventQuestion
from subscribe.forms import Registration, SubscribeForm, fill_subscription

from django.conf import settings


def _safe_string(s, max_len=32):
    safe = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ")
    return filter(lambda c: c in safe, s)[:max_len]

def register(request, slug):
    event = get_object_or_404(Event, slug=slug)
    now = datetime.datetime.now()
    if event.start_registration > now or event.end_registration < now:
        return HttpResponse(_("Inschrijving gesloten."))
    #SubscribeForm = SubscribeFormBuilder(event)
    if request.method == "POST":
        form = SubscribeForm(event, request.POST)
        if form.is_valid():
            # Store the data
            subscription = fill_subscription(form, event)
            if not subscription:
                # Error Filling subscription
                return HttpResponse(_("Error in saving form."))
            if subscription.event_option.price <= 0:
                subscription.payed = True
                subscription.send_confirmation_email()
                subscription.save()
                return HttpResponse(_("Dank voor uw inschrijving"))
            
            # You need to pay
            response = mollie.fetch(
                settings.MOLLIE['partner_id'],          # Partner id
                subscription.event_option.price,        # Amount
                form.cleaned_data["issuer"].safe_id(),  # Bank ID
                subscription.event_option.name,         # Description
                settings.MOLLIE['report_url'],          # Report url
                settings.MOLLIE['return_url']           # Return url
            )
            
            err = mollie.get_error(response)
            if err:
                return HttpResponse(_("Technische fout, probeer later opnieuw.") + "\n\n%d: %s" % (
                    err[0], err[1]
                ))
            
            subscription.trxid = response.order.transaction_id
            subscription.save()
            
            return HttpResponseRedirect(response.order.URL)

    else:
        form = SubscribeForm(event)
    c = {
        "event": event,
        "request": request,
        "form": form,
    }
    c.update(csrf(request))
    return render_to_response("form.html", c)

# called when the user returns from iDeal, is set as MERCHANTRETURNURL.
def returnPage(request):
    transaction_id = request.GET['transaction_id']
    
    try:
        subscription = Registration.objects.get(trxid=transaction_id)
    except:
        return HttpResponse(_("iDEAL error (onbekende inschrijving): Neem contact op met ict@jongedemocraten.nl. Controleer of uw betaling is afgeschreven alvorens de betaling opnieuw uit te voeren."))
    
    if subscription.payed and subscription.status == "Success":
        return HttpResponse(_("Betaling geslaagd. Ter bevestiging is een e-mail verstuurd."))
    elif subscription.status == "Cancelled":
        return HttpResponse(_("Je betaling is geannuleerd."))
    elif subscription.status == "Failure":
        return HttpResponse(_("Je betaling is om onbekende reden niet gelukt. Er is geen geld afgeschreven. Neem contact op met ict@jongedemocraten.nl of probeer het nogmaals."))
    elif subscription.status == "Expired":
        return HttpResponse(_("Je betaling is geannuleerd."))
    else:
        return HttpResponse(_("Er is een fout opgetreden bij het verwerken van je iDEAL transactie. Neem contact op met ict@jongedemocraten.nl of probeer het later nogmaals. Controleer of je betaling is afgeschreven alvorens de betaling opnieuw uit te voeren."))

         
def check(request):
    transaction_id = request.GET['transaction_id']
    
    response = mollie.check(settings.MOLLIE['partner_id'], transaction_id)  

    try:
        subscription = Registration.objects.get(trxid=transaction_id)
    except:
        logging.error("views::check() - cannot find subscription with transaction id: " + str(transaction_id))
        
    if response.order.status == "CheckedBefore":
        return
    elif response.order.payed and response.order.status == "Success": # Mollie gives payed=true and status=Success only once
        subscription.payed = True
        subscription.status = "Success"
        subscription.send_confirmation_email()
        subscription.save()
        return
    else:
        subscription.payed = False
        subscription.status = response.order.status
        subscription.save() 

          
# update the transaction status from the admin view
@login_required
def update_transaction_status(request):
    ec = request.GET['ec']
    subscription = Registration.objects.get(id=ec)
    trxid = subscription.trxid

    oIDC = iDEALConnector()
    
    req_status = oIDC.RequestTransactionStatus(trxid)
    
    if not req_status.IsResponseError():
        print 'views::update_transaction_status() : ' + str(req_status.getStatus())
        if req_status.getStatus() == IDEAL_TX_STATUS_SUCCESS:
            subscription.payed = True
            subscription.save()
            subscription.send_confirmation_email()
            return HttpResponse(_("Betaling geslaagd. Ter bevestiging is een e-mail verstuurd."))
        elif req_status.getStatus() == IDEAL_TX_STATUS_CANCELLED:
            return HttpResponse(_("Betaling is geannuleerd."))
        elif req_status.getStatus() == IDEAL_TX_STATUS_EXPIRED:
            return HttpResponse(_("Niet betaald. De transactie sessie is verlopen. Via deze transactie kan niet meer betaald worden."))
        elif req_status.getStatus() == IDEAL_TX_STATUS_OPEN:
            return HttpResponse(_("Nog niet betaald, maar de betaalsessie is nog niet verlopen."))
    else:
        return HttpResponse(_("Er was een probleem met de iDeal verbinding om de transactie status op te vragen. ERROR: " + req_status.getErrorMessage()))

@login_required
@commit_on_success # combines all database transactions and commits them on success
def update_all_event_transaction_statuses(request):
    print 'views::update_all_event_transaction_statuses()'
    eventId = request.GET['eventId']
    
    for r in Registration.objects.filter(event=eventId).filter(payed=False).filter(trxid__isnull=False).filter(check_ttl__gt=0):
        print 'view::update_all_event_transaction_statuses() - registration id: ' + str(r.id)
        r.check_payment_status()
        
    return HttpResponse(_("All event transactions/registrations statuses updated"))

    
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


