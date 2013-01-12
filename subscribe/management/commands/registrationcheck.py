from django.core.management.base import BaseCommand
from subscribe.models import Registration
import datetime

class Command(BaseCommand):
    def handle(self, *args, **options):
        now = datetime.datetime.now()
        days = 7
        seconds = 0
        
        # Get all registrations that are not payed, have a trixid and where 
        # check_ttl > 0 to check their payment status.        
        for r in Registration.objects.filter(payed=False).filter(trxid__isnull=False).filter(check_ttl__gt=0):
            # only check if the registration is not older than 7 days
            if (now > r.registration_date + datetime.timedelta(days, seconds)):
                r.check_payment_status()
