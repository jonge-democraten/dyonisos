from django.core.management.base import BaseCommand
from django.db.transaction import commit_on_success

from subscribe.models import IdealIssuer
import datetime

from lib.mollie import banklist

class Command(BaseCommand):
    
    @commit_on_success
    def handle(self, *args, **options):
    
        # Clean old issuers
        IdealIssuer.objects.all().delete()
        
        for (bank_id, bank_name) in banklist():
            issuer = IdealIssuer(issuer_id=bank_id, name=bank_name)
            issuer.save()
            print "%d\t%s" % (bank_id, bank_name)
        return
        
