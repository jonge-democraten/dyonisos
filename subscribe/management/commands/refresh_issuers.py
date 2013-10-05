from django.core.management.base import BaseCommand
from django.db.transaction import commit_on_success

from subscribe.models import IdealIssuer
import datetime

from lib import mollie

class Command(BaseCommand):
    
    @commit_on_success
    def handle(self, *args, **options):
    
        # Clean old issuers
        IdealIssuer.objects.all().delete()
        
        for bank in mollie.banklist():
            issuer = IdealIssuer(issuer_id=bank.bank_id, name=bank.bank_name)
            issuer.save()
            print "%d\t%s" % (bank.bank_id, bank.bank_name)
        return
        
