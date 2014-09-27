from subscribe.views import HomeView

from django.conf.urls.defaults import include, patterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Inschrijf formulier
    (r'^$', HomeView.as_view()),
    (r'^inschrijven/(?P<slug>[\w-]+)/$', 'subscribe.views.register'),

    (r'^report/$', 'subscribe.views.check'), # this is the merchant return url
    (r'^return/$', 'subscribe.views.return_page'), # this is the merchant return url
    (r'^deleteEventQuestion/$', 'subscribe.views.delete_event_question'),

    # Uncomment the admin/doc line below to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
