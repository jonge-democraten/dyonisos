from django.conf.urls import url, include
from django.contrib import admin

from subscribe.views import HomeView

urlpatterns = [
    url(r'^$', HomeView.as_view()),
    url(r'^inschrijven/(?P<slug>[\w-]+)/$', 'subscribe.views.register'), # Inschrijf formulier

    url(r'^report/$', 'subscribe.views.check'), # this is the merchant return url
    url(r'^return/$', 'subscribe.views.return_page'), # this is the merchant return url
    url(r'^deleteEventQuestion/$', 'subscribe.views.delete_event_question'),

    url(r'^admin/', include(admin.site.urls)),
]
