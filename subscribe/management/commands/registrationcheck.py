from django.core.management.base import BaseCommand, CommandError
from subscribe.models import *

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Get all registrations that are not payed, have a trixid and where 
        # check_ttl > 0 to check their payment status.
        for r in Registration.objects.filter(payed=False).filter(trxid__isnull=False).filter(check_ttl__gt=0):
            r.check_payment_status()

