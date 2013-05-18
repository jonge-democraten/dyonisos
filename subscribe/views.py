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

from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.db.transaction import commit_on_success

from subscribe.models import Event, EventOption, EventQuestion
from subscribe.forms import IdealIssuer, Registration, SubscribeForm, fill_subscription

from lib.ideal import *


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
            oIDC = iDEALConnector()

            req = oIDC.RequestTransaction(
                issuerId=form.cleaned_data["issuer"].safe_id(),
                purchaseId=subscription.gen_subscription_id(),
                amount=subscription.event_option.price,
                description=_safe_string(subscription.event_option.__unicode__()),
                entranceCode=subscription.gen_subscription_id() )
            
            if type(req) != AcquirerTransactionResponse:
                return HttpResponse(_("Technische fout, probeer later opnieuw."))
            
            sUrl = req.getIssuerAuthenticationURL()
            
            # store the transaction ID, can later be used to check the status of the transaction
            transactionId = req.getTransactionID()
            subscription.trxid = transactionId
            subscription.save()
            
            return HttpResponseRedirect(sUrl)
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
def check(request):
    trxid = request.GET['trxid']
    try:
        ec = int(request.GET['ec'].split("x")[0])
    except:
        return HttpResponse(_("iDEAL error(Technische fout): Neem contact op met ict@jongedemocraten.nl. Controleer of uw betaling is afgeschreven alvorens de betaling opnieuw uit te voeren."))

    oIDC = iDEALConnector()
    req_status = oIDC.RequestTransactionStatus(trxid)

    if not req_status.IsResponseError():
        try:
            subscription = Registration.objects.get(id=ec)
        except:
            return HttpResponse(_("iDEAL error (onbekende inschrijving): Neem contact op met ict@jongedemocraten.nl. Controleer of uw betaling is afgeschreven alvorens de betaling opnieuw uit te voeren."))
        if req_status.getStatus() == IDEAL_TX_STATUS_SUCCESS:
            subscription.payed = True
            subscription.send_confirmation_email()
            subscription.save()
            return HttpResponse(_("Betaling geslaagd. Ter bevestiging is een e-mail verstuurd."))
        elif req_status.getStatus() == IDEAL_TX_STATUS_CANCELLED:
            return HttpResponse(_("Je betaling is geannuleerd."))
        else:
            return HttpResponse(_("Er is een fout opgetreden bij het verwerken van je iDEAL transactie. Neem contact op met ict@jongedemocraten.nl of probeer het later nogmaals. Controleer of je betaling is afgeschreven alvorens de betaling opnieuw uit te voeren."))
    else:
        return HttpResponse(_("Er is een fout opgetreden bij het verwerken van je iDEAL transactie. Neem contact op met ict@jongedemocraten.nl of probeer het later nogmaals. Controleer of je betaling is afgeschreven alvorens de betaling opnieuw uit te voeren."))


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
def delete_event_option(request):
    optionId = request.GET['optionId']
    
    usedInNRegistrations = Registration.objects.filter(event_option=optionId).count()
    
    if (usedInNRegistrations != 0):
        return HttpResponse(_("Dit event option kan niet verwijderd worden omdat deze al gebruikt wordt in " + str(usedInNRegistrations) +
                              " aanmeldingen. <br /> Verwijdering van dit event option zou deze aanmeldingen ongeldig maken en is daarom niet mogelijk."))
    else:
        eventOption = EventOption.objects.get(pk=optionId)
        eventOption.delete()
        
        return HttpResponse(_("Event option werd nog niet gebruikt in een aanmelding en kon daarom succesvol verwijderd worden."))
    
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


