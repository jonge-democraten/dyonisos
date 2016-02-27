from django.conf.urls import url
from subscribe import views


urlpatterns = [
    url(r'^$', views.HomeView.as_view()),
    url(r'^inschrijven/(?P<slug>[\w-]+)/$', views.register),
    url(r'^deleteEventQuestion/$', views.delete_event_question),
    url(r'^webhook/(?P<id>\d+)/?$', views.webhook, name='webhook'),
    url(r'^return/(?P<id>\d+)/?$', views.return_page, name='return_page'),
]
