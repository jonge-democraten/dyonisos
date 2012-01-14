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
from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.core.context_processors import csrf

from Dyonisos.subscribe.models import *
from Dyonisos.subscribe.forms import *

from Dyonisos.lib.ideal import *


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
                entranceCode=subscription.gen_subscription_id()
            )
            if type(req) != AcquirerTransactionResponse:
                return HttpResponse(_("Technische fout, probeer later opnieuw."))
            sUrl = req.getIssuerAuthenticationURL()
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

def refresh_issuers(request):
    oldest_issuer = IdealIssuer.objects.order_by('update')
    if oldest_issuer:
        if (oldest_issuer[0].update - datetime.datetime.now()).days <= 0:
            # Don't update more than once a day.
            return HttpResponse(_("Don't refresh more that once a day. Try again later."))
    # Get the new Ideal issuer list
    oIDC = iDEALConnector()
    issuers = oIDC.GetIssuerList()
    if issuers.IsResponseError():
        # An error occured
        print "Error getting Ideal issuers: %s - %s" % (issuers.getErrorCode(), issuers.getErrorMessage())
        return HttpResponse(_("An error occured while getting the issuers list."))
    dIssuers = issuers.getIssuerFullList()
    for sIS, oIS in dIssuers.items():
        issuer = IdealIssuer.objects.filter(issuer_id=oIS.getIssuerID())
        if issuer:
            issuer = issuer[0]
        else:
            issuer = IdealIssuer()
            issuer.issuer_id = oIS.getIssuerID()
        issuer.name = oIS.getIssuerName()
        issuer.list_type = oIS.getIssuerListType()
        issuer.save()
    # Now delete older issuers
    IdealIssuer.objects.filter(update__lte=datetime.datetime.now()+datetime.timedelta(-1,0,0)).delete()
    return HttpResponse(_("Update succesfull."))


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








