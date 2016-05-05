from os import environ as env

from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template import Context, Template
from django import forms

from twilio.rest import TwilioRestClient
from twilio import twiml
import requests
import logging

from cabot.plugins.models import AlertPlugin

telephone_template = "This is an urgent message from Arachnys monitoring. Service \"{{ service.name }}\" is erroring. Please check Cabot urgently."
sms_template = "Service {{ service.name }} {% if service.overall_status == service.PASSING_STATUS %}is back to normal{% else %}reporting {{ service.overall_status }} status{% endif %}: {{ scheme }}://{{ host }}{% url 'service' pk=service.id %}"

logger = logging.getLogger(__name__)

class TwilioPhoneCall(AlertPlugin):
    name = "Twilio Phone Call"
    slug = "twilio_phone"
    author = "Jonathan Balls"

    def send_alert(self, service, users, duty_officers):

        account_sid = env.get('TWILIO_ACCOUNT_SID')
        auth_token  = env.get('TWILIO_AUTH_TOKEN')
        outgoing_number = env.get('TWILIO_OUTGOING_NUMBER')
        url = 'http://%s%s' % (settings.WWW_HTTP_HOST,
                               reverse('twiml-callback', kwargs={'service_id': service.id}))

        # No need to call to say things are resolved
        if service.overall_status != service.CRITICAL_STATUS:
            return
        client = TwilioRestClient(
            account_sid, auth_token)

        mobiles = TwilioUserData.objects.filter(user__user__in=duty_officers)
        mobiles = [m.prefixed_phone_number for m in mobiles if m.phone_number]
        for mobile in mobiles:
            try:
                client.calls.create(
                    to=mobile,
                    from_=outgoing_number,
                    url=url,
                    method='GET',
                )
            except Exception, e:
                logger.exception('Error making twilio phone call: %s' % e)

class TwilioSMS(AlertPlugin):
    name = "Twilio SMS"
    slug = "twilio_sms"
    author = "Jonathan Balls"

    def send_alert(self, service, users, duty_officers):

        account_sid = env.get('TWILIO_ACCOUNT_SID')
        auth_token  = env.get('TWILIO_AUTH_TOKEN')
        outgoing_number = env.get('TWILIO_OUTGOING_NUMBER')

        all_users = list(users) + list(duty_officers)

        client = TwilioRestClient(
            account_sid, auth_token)
        mobiles = TwilioUserData.objects.filter(user__user__in=all_users)
        mobiles = [m.prefixed_phone_number for m in mobiles if m.phone_number]
        c = Context({
            'service': service,
            'host': settings.WWW_HTTP_HOST,
            'scheme': settings.WWW_SCHEME,
        })
        message = Template(sms_template).render(c)
        for mobile in mobiles:
            try:
                client.sms.messages.create(
                    to=mobile,
                    from_=outgoing_number,
                    body=message,
                )
            except Exception, e:
                logger.exception('Error sending twilio sms: %s' % e)

class TwilioUserData(forms.Form):
    name = "Twilio Plugin"
    phone_number = forms.CharField(max_length=30)

    def save(self, *args, **kwargs):
        if str(self.phone_number).startswith('+'):
            self.phone_number = self.phone_number[1:]
        return super(TwilioUserData, self).save(*args, **kwargs)

    @property
    def prefixed_phone_number(self):
        return '+%s' % self.phone_number
