from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings
from cabot.cabotapp.tests.tests_basic import LocalTestCase
from cabot.plugins.models import AlertPluginModel
from mock import Mock, patch
from os import environ as env

from cabot.cabotapp.models import Service
from cabot_alert_twilio import plugin


class TestTwilioPhoneCallAlert(LocalTestCase):
    def setUp(self):
        super(TestTwilioPhoneCallAlert, self).setUp()

        self.twilio_call_alert, created = AlertPluginModel.objects.get_or_create(
                slug='twilio_phone')

        u = User.objects.get(pk=self.user.pk)
        self.user_phone_number = '+123456789'
        u.twilio_phone_settings.phone_number = self.user_phone_number
        
        self.service.users_to_notify.add(self.user)
        self.service.alerts.add(self.twilio_call_alert)
        self.service.save()
        self.service.update_status()

    def test_users_to_notify(self):
        self.assertEqual(self.service.users_to_notify.all().count(), 1)
        self.assertEqual(self.service.users_to_notify.get(pk=1).username, self.user.username)
    
    @patch('cabot_alert_twilio.plugin.TwilioRestClient')
    def test_normal_phone_alert(self, fake_twilio_rest_client):
        self.service.overall_status = Service.PASSING_STATUS
        self.service.old_overall_status = Service.ERROR_STATUS
        self.service.save()
        self.service.alert()
        self.assertFalse(fake_twilio_rest_client.called)

    @patch('cabot_alert_twilio.plugin.TwilioRestClient')
    def test_failure_phone_alert(self, fake_twilio_rest_client):
        # Most recent failed
        self.service.overall_status = Service.CRITICAL_STATUS
        self.service.old_overall_status = Service.PASSING_STATUS
        self.service.save()
        self.service.alert()
        url = 'http://%s%s' % (settings.WWW_HTTP_HOST,
            reverse('twiml-callback', kwargs={'service_id': self.service.id}))
        fake_twilio_rest_client.return_value.calls.create.assert_called_with(
            to=self.user_phone_number,
            from_=env.get('TWILIO_OUTGOING_NUMBER'),
            method='GET',
            url=url
        )

class TestTwilioSMSAlert(LocalTestCase):
    def setUp(self):
        super(TestTwilioSMSAlert, self).setUp()

        self.twilio_sms_alert, created = AlertPluginModel.objects.get_or_create(
                slug='twilio_sms')

        u = User.objects.get(pk=self.user.pk)
        self.user_phone_number = '+123456789'
        u.twilio_phone_settings.phone_number = self.user_phone_number
        
        self.service.users_to_notify.add(self.user)
        self.service.alerts.add(self.twilio_sms_alert)
        self.service.save()
        self.service.update_status()

    def test_users_to_notify(self):
        self.assertEqual(self.service.users_to_notify.all().count(), 1)
        self.assertEqual(self.service.users_to_notify.get(pk=1).username, self.user.username)
    
    @patch('cabot_alert_twilio.plugin.TwilioRestClient')
    def test_normal_sms_alert(self, fake_twilio_rest_client):
        self.service.overall_status = Service.PASSING_STATUS
        self.service.old_overall_status = Service.ERROR_STATUS
        self.service.save()
        self.service.alert()
        fake_twilio_rest_client.return_value.sms.messages.create.assert_called_with(
             to=self.user_phone_number,
             from_=env.get('TWILIO_OUTGOING_NUMBER'),
             body='Service Service is back to normal: http://{}/service/1/'.format(
                settings.WWW_HTTP_HOST)
            )

    @patch('cabot_alert_twilio.plugin.TwilioRestClient')
    def test_failure_sms_alert(self, fake_twilio_rest_client):
        # Most recent failed
        self.service.overall_status = Service.CRITICAL_STATUS
        self.service.old_overall_status = Service.PASSING_STATUS
        self.service.save()
        self.service.alert()
        url = 'http://%s%s' % (settings.WWW_HTTP_HOST,
            reverse('twiml-callback', kwargs={'service_id': self.service.id}))
        fake_twilio_rest_client.return_value.sms.messages.create.assert_called_with(
            to=self.user_phone_number,
            from_=env.get('TWILIO_OUTGOING_NUMBER'),
            body=u'Service Service reporting CRITICAL status: http://{}/service/1/'.format(
                settings.WWW_HTTP_HOST)
        )

