from django.conf import settings
from django.test import TestCase
from django.test import Client
from django.urls import reverse

from subscribe.models import Event
from subscribe.models import Registration
from subscribe.forms import SubscribeForm


class TestUserPages(TestCase):
    """Test case with client for pages for normal user"""
    fixtures = ['test_data.json']

    def setUp(self):
        self.client = Client()

    def test_view_homepage(self):
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 200)

    def test_view_subscribe_page(self):
        events = Event.objects.all()
        self.assertTrue(events.exists())
        for event in events:
            response = self.client.get(reverse('subscribe', kwargs={'slug': event.slug}))
            self.assertEqual(response.status_code, 200)

    def test_subscribe_form(self):
        events = Event.objects.all()
        self.assertTrue(events.exists())
        for event in events:
            form_data = {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@doe.com',
            }
            form = SubscribeForm(event=event, data=form_data)
            self.assertTrue(form.is_valid())

    def test_subscribe_form_empty_email(self):
        events = Event.objects.all()
        self.assertTrue(events.exists())
        for event in events:
            form_data = {
                'first_name': '',
                'last_name': '',
                'email': 'john@doe.com',
            }
            form = SubscribeForm(event=event, data=form_data)
            self.assertFalse(form.is_valid())


class TestCaseAdminLogin(TestCase):
    """Test case with client and login as admin function"""
    fixtures = ['test_data.json']

    def setUp(self):
        self.client = Client()
        self.login()

    def login(self):
        """Login as admin."""
        success = self.client.login(username='admin', password='admin123')
        self.assertTrue(success)
        response = self.client.get('/admin/', follow=True)
        self.assertEqual(response.status_code, 200)
        return response


class TestAdminPages(TestCaseAdminLogin):

    def test_events_page(self):
        response = self.client.get('/admin/subscribe/event/')
        self.assertEqual(response.status_code, 200)

    def test_event_edit_pages(self):
        events = Event.objects.all()
        self.assertTrue(events.exists())
        for event in events:
            response = self.client.get('/admin/subscribe/event/' + str(event.id) + '/change/')
            self.assertEqual(response.status_code, 200)

    def test_registrations_page(self):
        response = self.client.get('/admin/subscribe/registration/')
        self.assertEqual(response.status_code, 200)

    def test_registration_page(self):
        registrations = Registration.objects.all()
        self.assertTrue(registrations.exists())
        for registration in registrations:
            response = self.client.get('/admin/subscribe/registration/' + str(registration.id) + '/change/')
            self.assertEqual(response.status_code, 200)


