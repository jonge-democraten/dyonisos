import datetime
import logging
import Mollie

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.list import ListView

from subscribe.models import Event, EventQuestion
from subscribe.forms import Registration, SubscribeForm, fill_subscription


def event_message(request, event, message):
    c = {"event": event, "request": request, "message": message}
    return render_to_response("subscribe/event_message.html", c)


def register(request, slug):
    logger = logging.getLogger(__name__)

    # Get the event
    event = get_object_or_404(Event, slug=slug)

    # If not staff, check if allowed
    if not request.user.is_staff:
        now = datetime.datetime.now()
        if event.start_registration > now or event.end_registration < now:
            return event_message(request, event, _("Inschrijving gesloten."))
        if event.is_full():
            return event_message(request, event, _("Helaas is het maximum aantal inschrijvingen bereikt."))

    # If this is not a POST request
    if request.method != "POST":
        # then just create the form...
        form = SubscribeForm(event)
        c = {"event": event, "request": request, "form": form, "user_is_staff": request.user.is_staff}
        c.update(csrf(request))
        return render_to_response("subscribe/form.html", c)

    # It is a POST request, check if the form is valid...
    form = SubscribeForm(event, request.POST)
    if not form.is_valid():
        c = {"event": event, "request": request, "form": form, "user_is_staff": request.user.is_staff}
        c.update(csrf(request))
        return render_to_response("subscribe/form.html", c)

    # It is a POST request, and the form is valid, check if this is the confirmation page
    if 'registration_preview' not in request.POST:
        form.confirm_page()
        c = {"event": event, "request": request, "form": form, "user_is_staff": request.user.is_staff}
        c.update(csrf(request))
        return render_to_response("subscribe/form.html", c)

    # Maybe this is just a test of the confirmation email?
    if 'testsubmit' in request.POST:
        subscription = fill_subscription(form, event)
        msg = subscription.send_confirmation_email()
        subscription.delete()
        msg = '<br/>'.join(escape(msg).split('\n'))
        return event_message(request, event, mark_safe("De volgende email is verstuurd:<br/><br/>{}".format(msg)))

    # We confirmed. Create the subscription in the database...
    subscription = fill_subscription(form, event)

    # Check if the subscription form could be saved
    if not subscription:
        # Error Filling subscription
        error_str = "Error in saving form."
        return HttpResponse(_(error_str))

    # Check (again) if maybe the number of registrations is over the limit...
    if subscription in event.get_registrations_over_limit():
        subscription.delete()
        if event.is_full():
            error_str = "De inschrijving kan niet worden voltooid, omdat het maximum aantal inschrijvingen is bereikt."
        else:
            error_str = "De inschrijving kan niet worden voltooid, omdat een van de gekozen opties het maximum aantal inschrijvingen heeft bereikt."
        return event_message(request, event, _(error_str))

    # Check if we need to pay or not...
    if subscription.price <= 0:
        subscription.paid = True
        subscription.send_confirmation_email()
        subscription.save()
        return event_message(request, event, _("Inschrijving geslaagd. Ter bevestiging is een e-mail verstuurd."))

    # Payment required...
    try:
        mollie = Mollie.API.Client()
        mollie.setApiKey(settings.MOLLIE_KEY)

        # METADATA TOEVOEGEN
        webhookUrl = request.build_absolute_uri(reverse("webhook", args=[subscription.id]))
        redirectUrl = request.build_absolute_uri(reverse("return_page", args=[subscription.id])) 

        payment = mollie.payments.create({
            'amount': float(subscription.price) / 100.0,
            'description': subscription.event.name,
            'webhookUrl': webhookUrl,
            'redirectUrl': redirectUrl,
        })

        subscription.trxid = payment["id"]
        subscription.save()

        return HttpResponseRedirect(payment.getPaymentUrl())
    except Mollie.API.Error as e:
        error_str = "register: Technische fout, probeer later opnieuw.\n\n" + e.message
        logger.error(error_str)
        return event_message(request, event, _(error_str))


def check_transaction(subscription):
    logger = logging.getLogger(__name__)
    logger.info('check_transaction: Checking transaction %d with id %s' % (subscription.id, subscription.trxid))

    mollie = Mollie.API.Client()
    mollie.setApiKey(settings.MOLLIE_KEY)
    payment = mollie.payments.get(subscription.trxid)

    logger.info("check_transaction: Transaction %s has status %s" % (subscription.id, payment['status']))

    subscription.status = payment['status']
    subscription.paid = payment.isPaid()
    subscription.save()
    if subscription.paid:
        subscription.send_confirmation_email()


# called when the user returns from Mollie
def return_page(request, id):
    logger = logging.getLogger(__name__)
    logger.info('views::return_page() - registration id: ' + str(id))

    # Retrieve the registration
    try:
        subscription = Registration.objects.get(id=id)
    except:
        return HttpResponse(_("iDEAL error (onbekende inschrijving): Neem contact op met ict@jongedemocraten.nl. Controleer of uw betaling is afgeschreven alvorens de betaling opnieuw uit te voeren."))

    # If status unknown, then check it...
    if subscription.status == "":
        try:
            check_transaction(subscription)
        except Mollie.API.Error as e:
            error_str = "return_page: Technische fout, probeer later opnieuw." + "\n\n%s" % (e.message,)
            logger.error(error_str)
            return event_message(request, subscription.event, _(error_str))

    if subscription.status == "paid":
        return event_message(request, subscription.event, _("Betaling geslaagd. Ter bevestiging is een e-mail verstuurd."))
    elif subscription.status == "cancelled" or subscription.status == "expired":
        return event_message(request, subscription.event, _("Je betaling is geannuleerd."))
    elif subscription.status == "open" or subscription.status == "pending":
        return event_message(request, subscription.event, _("Je betaling staat geregistreerd in ons systeem, maar wordt nog verwerkt door onze bank. Als je binnen een uur geen bevestigingsmail ontvangt, is er mogelijk iets fout gegaan met de betaling. Neem in dat geval contact op met ict@jongedemocraten.nl."))
    else:
        return event_message(request, subscription.event, _("Er is een fout opgetreden bij het verwerken van je iDEAL transactie. Neem contact op met ict@jongedemocraten.nl of probeer het later nogmaals. Controleer of je betaling is afgeschreven alvorens de betaling opnieuw uit te voeren."))


@csrf_exempt
def webhook(request, id):
    # trigger checking
    if request.method == "POST":
        transaction_id = request.POST['id']
    else:
        transaction_id = request.GET['id']

    logger = logging.getLogger(__name__)
    logger.info('views::check() - id: %s, transaction id: %s' % (id, transaction_id))

    try:
        subscription = Registration.objects.get(id=id, trxid=transaction_id)
    except:
        logger.error("views::check() - cannot find matching subscription")
        return HttpResponse(_("NOT OK"))

    try:
        check_transaction(subscription)
    except Mollie.API.Error as e:
        logger.error("webhook: error %s" % (e.message,))

    return HttpResponse(_("OK"))


@login_required
def delete_event_question(request):
    questionId = request.GET['questionId']
    warning = int(request.GET['warning'])

    if warning == 0:
        eventQuestion = EventQuestion.objects.get(pk=questionId)
        eventQuestion.delete()
        return HttpResponse(_('Vraag verwijderd. <br /> <a href="/admin/">Terug naar admin.</a>'))
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
