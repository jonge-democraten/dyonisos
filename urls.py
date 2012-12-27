from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Inschrijf formulier
    (r'^inschrijven/(?P<slug>[\w-]+)/$', 'subscribe.views.register'),

    (r'^check/$', 'subscribe.views.check'),
    (r'^refresh_issuers/$', 'subscribe.views.refresh_issuers'),
    (r'^updateEventTransactionStatuses/$', 'subscribe.views.update_all_event_transaction_statuses'),

    # Uncomment the admin/doc line below to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
