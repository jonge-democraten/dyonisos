from django.test import TestCase

import Mollie
import subscribe.views


class TestPayment(TestCase):

    def test_is_paid(self):
        """
        tests the rather unexpected return value of Mollie Payment isPaid()
        (https://github.com/mollie/mollie-api-python/issues/18)
        note: isPaid() returns a date, empty string or False
        """
        payment = Mollie.API.Payment()
        self.assertEqual(payment.isPaid(), False)
        self.assertEqual(subscribe.views.is_paid(payment), False)
        payment['paidDatetime'] = ''
        self.assertEqual(payment.isPaid(), '')
        self.assertEqual(subscribe.views.is_paid(payment), False)
        payment['paidDatetime'] = '2016-12-25'
        self.assertEqual(payment.isPaid(), '2016-12-25')
        self.assertEqual(subscribe.views.is_paid(payment), True)
