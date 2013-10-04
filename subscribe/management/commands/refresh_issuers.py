from django.core.management.base import BaseCommand
from django.db.transaction import commit_on_success

from subscribe.models import IdealIssuer
import datetime

import pycurl
import cStringIO
from lxml import objectify

class Command(BaseCommand):
    
    @commit_on_success
    def handle(self, *args, **options):
    
        # Clean old issuers
        IdealIssuer.objects.all().delete()
        
        buf = cStringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(c.URL, 'https://secure.mollie.nl/xml/ideal?a=banklist')
        c.setopt(c.WRITEFUNCTION, buf.write)
        c.setopt(c.SSL_VERIFYHOST, 2)
        c.perform()
        
        response = objectify.fromstring(buf.getvalue())
        print response.message
        for bank in response.bank:
            issuer = IdealIssuer(issuer_id=bank.bank_id, name=bank.bank_name)
            issuer.save()
            print "%d\t%s" % (bank.bank_id, bank.bank_name)
        
        buf.close()
        return
        
