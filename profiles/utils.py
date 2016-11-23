from social.pipeline.user import get_username as social_get_username
from random import randrange
from django.conf import settings
import requests

from rest_framework.metadata import BaseMetadata

def get_username(strategy, details, user=None, *args, **kwargs):
  result = social_get_username(strategy, details, user=user, *args, **kwargs)

  # result['username'] = '-'.join([
  #     result['username'], strategy.backend.name, str(randrange(0, 1000))
  # ])
  return result

def send_email(to, subject, text, *args, **kw):
    # to = 'alan@firstcodeacademy.com'
    print 'sending mail to {}'.format(to)
    return requests.post(
        settings.MAILGUN_API_URL,
        # "https://api.mailgun.net/v3/sandbox1862316f0fcf4acdb68a9250cbba6270.mailgun.org/messages",
        auth=("api", settings.MAILGUN_KEY),
        data={"from": settings.DEFAULT_FROM_EMAIL,
              "to": to,
              "subject": subject,
              "text": text,
              # "subject": "Hello Alan Hau",
              # "text": "Congratulations Alan Hau, you just sent an email with Mailgun!  You are truly awesome!  You can see a record of this email in your logs: https://mailgun.com/cp/log .  You can send up to 300 emails/day from this sandbox server.  Next, you should add your own domain so you can send 10,000 emails/month for free."
              })



class MinimalMetadata(BaseMetadata):
    """
    Don't include field and other information for `OPTIONS` requests.
    Just return the name and description.
    """
    def determine_metadata(self, request, view):
        return {
            'name': view.get_view_name(),
            'description': view.get_view_description()
        }

