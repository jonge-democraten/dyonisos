from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^jdideal/', include('jdideal.foo.urls')),

    # Inschrijf formulier
    (r'^inschrijven/(?P<slug>[\w-]+)/$', 'jdideal.subscribe.views.register'),
    #(r'^form/(?P<slug>[\w-]+)/$', 'jdideal.subscribe.views.register'),

    (r'^check/$', 'jdideal.subscribe.views.check'),
    (r'^refresh_issuers/$', 'jdideal.subscribe.views.refresh_issuers'),

    # Uncomment the admin/doc line below to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
