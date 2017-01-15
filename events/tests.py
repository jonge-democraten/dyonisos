from django.conf import settings
from django.test import TestCase
from django.test import Client

from subscribe.models import Event


class TestCaseAdminLogin(TestCase):
    """Test case with client and login as admin function."""
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

    def test_event_edit_pages(self):
        events = Event.objects.all()
        for event in events:
            response = self.client.get('/admin/subscribe/event/' + str(event.id) + '/change/')
            self.assertEqual(response.status_code, 200)
