from django.core.management.base import BaseCommand
from django.db import transaction

from subscribe.models import IdealIssuer

from lib import mollie


# command to update bank list (ideal issuers)
# run as 'python manage.py refresh_issuers'
class Command(BaseCommand):

    @transaction.atomic
    def handle(self, *args, **options):

        # Clean old issuers
        IdealIssuer.objects.all().delete()

        for bank in mollie.banklist():
            issuer = IdealIssuer(issuer_id=bank.bank_id, name=bank.bank_name)
            issuer.save()
            print "%d\t%s" % (bank.bank_id, bank.bank_name)
