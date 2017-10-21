from django.test import TestCase

import Mollie
import subscribe.views


class TestPayment(TestCase):

    def test_is_paid(self):
        """
        tests to check payment status, originally introduced for bug in Mollie api (fixed in 1.2)
        """
        payment = Mollie.API.Payment()
        self.assertEqual(payment.isPaid(), False)
        self.assertEqual(subscribe.views.is_paid(payment), False)
        payment['paidDatetime'] = ''
        self.assertEqual(payment.isPaid(), False)
        self.assertEqual(subscribe.views.is_paid(payment), False)
        payment['paidDatetime'] = '2016-12-25'
        self.assertEqual(payment.isPaid(), True)
        self.assertEqual(subscribe.views.is_paid(payment), True)
