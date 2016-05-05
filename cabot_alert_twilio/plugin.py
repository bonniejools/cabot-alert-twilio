from os import environ as env

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import Context, Template
from django import forms

from twilio.rest import TwilioRestClient
from twilio import twiml
import requests
import logging

from cabot.plugins.models import AlertPlugin, AlertPluginModel

telephone_template = "This is an urgent message from Arachnys monitoring. Service \"{{ service.name }}\" is erroring. Please check Cabot urgently."
sms_template = "Service {{ service.name }} {% if service.overall_status == service.PASSING_STATUS %}is back to normal{% else %}reporting {{ service.overall_status }} status{% endif %}: {{ scheme }}://{{ host }}{% url 'service' pk=service.id %}"

logger = logging.getLogger(__name__)

# We will attach this to TwilioPhoneCallAlert but it will be accessed
# by both plugins
class TwilioUserSettingsForm(forms.Form):
    name = "Twilio Plugin"
    phone_number = forms.CharField(max_length=30)

    def clean(self, *args, **kwargs):
	phone_number = self.cleaned_data['phone_number']
        if not phone_number.startswith('+'):
            self.cleaned_data['phone_number'] = '+{}'.format(phone_number)
        return super(TwilioUserSettingsForm, self).clean()


class TwilioPhoneCallAlert(AlertPlugin):
    name = "Twilio Phone Call"
    slug = "twilio_phone"
    author = "Jonathan Balls"
    version = "0.0.1"

    plugin_variables = [
        'TWILIO_ACCOUNT_SID',
	'TWILIO_AUTH_TOKEN',
	'TWILIO_OUTGOING_NUMBER'
    ]

    user_config_form = TwilioUserSettingsForm

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

	mobiles = [self.plugin_model.get_user_variable(u, 'phone_number') for u in users]

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


class TwilioSMSAlert(AlertPlugin):
    name = "Twilio SMS"
    slug = "twilio_sms"
    author = "Jonathan Balls"
    version = "0.0.1"

    plugin_variables = [
        'TWILIO_ACCOUNT_SID',
	'TWILIO_AUTH_TOKEN',
	'TWILIO_OUTGOING_NUMBER'
    ]

    def send_alert(self, service, users, duty_officers):

        account_sid = env.get('TWILIO_ACCOUNT_SID')
        auth_token  = env.get('TWILIO_AUTH_TOKEN')
        outgoing_number = env.get('TWILIO_OUTGOING_NUMBER')

        all_users = list(users) + list(duty_officers)

        client = TwilioRestClient(
            account_sid, auth_token)
	twilio_phone_plugin = AlertPluginModel.objects.get(slug='twilio_phone')
	mobiles = [twilio_phone_plugin.get_user_variable(u, 'phone_number') for u in users]
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

