from django.conf.urls import patterns, include, url
from .views import twiml_callback

urlpatterns = patterns('',
    url(r'^twiml_callback/(?P<service_id>\d+)/', twiml_callback, name="twiml-callback"),
)

