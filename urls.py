from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Inschrijf formulier
    (r'^inschrijven/(?P<slug>[\w-]+)/$', 'Dyonisos.subscribe.views.register'),

    (r'^check/$', 'Dyonisos.subscribe.views.check'),
    (r'^refresh_issuers/$', 'Dyonisos.subscribe.views.refresh_issuers'),

    # Uncomment the admin/doc line below to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
