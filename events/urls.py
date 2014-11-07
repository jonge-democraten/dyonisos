from django.conf.urls import patterns, include, url
from django.contrib import admin

from subscribe.views import HomeView

urlpatterns = patterns('',
    (r'^$', HomeView.as_view()),
    (r'^inschrijven/(?P<slug>[\w-]+)/$', 'subscribe.views.register'), # Inschrijf formulier

    (r'^report/$', 'subscribe.views.check'), # this is the merchant return url
    (r'^return/$', 'subscribe.views.return_page'), # this is the merchant return url
    (r'^deleteEventQuestion/$', 'subscribe.views.delete_event_question'),

    # Uncomment the admin/doc line below to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
