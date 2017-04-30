from social.pipeline.user import get_username as social_get_username
from random import randrange
from django.conf import settings
import requests

from rest_framework.metadata import BaseMetadata

from math import radians, cos, sin, asin, sqrt




def haversine(lon1, lat1, lon2, lat2):
  """
  Calculate the great circle distance between two points 
  on the earth (specified in decimal degrees)
  """
  # convert decimal degrees to radians 
  lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
  # haversine formula 
  dlon = lon2 - lon1 
  dlat = lat2 - lat1 
  a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
  c = 2 * asin(sqrt(a)) 
  km = 6367 * c
  return km

def get_closestSubdomainByCoord(lon, lat):
  """
  given lat/lon coords, return a string representing the closest subdomain (ie. hk, sg, tw)
  """
  distanceList = [ (k, haversine(lon, lat, v.get('lon'), v.get('lat')) ) for k,v in settings.SUBDOMAINSPECIFICMAPPING.iteritems()]

  minTuple = min(distanceList, key = lambda x: x[1])

  return minTuple[0]


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

import json
from django.template.loader import render_to_string

def send_referral_email(senderUser, emailStr  ):
  """
  base function for sending email
  """
  email_dict_JSON = json.dumps({
    k: {} for k in filter(lambda x: x , emailStr.split(','))
  })

  emailFrom = senderUser.email

  if not emailFrom:
    # some users may not have email
    emailFrom = settings.DEFAULT_FROM_EMAIL


  # text = render_to_string('my_template.html', {'foo': 'bar'})
  # render_to_string("account/email/internal_receipt.txt", context).strip()

  preferredSubdomain = senderUser.preferredSubdomain()
  s = settings.SUBDOMAINSPECIFICMAPPING.get(preferredSubdomain)

  context = {
    'senderUser': senderUser,
    'formattedReferralAmt': "{} {}".format(s.get('currency'), s.get('refDiscount')),
    'officeLocation': s.get('officeLocation'),
    'officePhone': s.get('officePhone'),
    'emailFrom': s.get('emailFrom'),
    'preferredSubdomain': senderUser.preferredSubdomain(),
    'link': 'https://{}.firstcodeacademy.com/en/programs/referred'.format(senderUser.preferredSubdomain()),
  }


  html = render_to_string("account/email/referral.html", context).strip()
  text = render_to_string("account/email/referral.txt", context).strip()

  print 'send_referral_email: {}, {}'.format(senderUser.email, emailStr)


  r = requests.post(
    settings.MAILGUN_API_URL,
    auth=("api", settings.MAILGUN_KEY),
    data={"from": senderUser.email,
          "h:Reply-To": senderUser.email,
          "to": emailStr,

          "recipient-variables": email_dict_JSON,

          "subject": "{} has referred you to First Code Academy".format(senderUser.displayName),
          "text": text,
          "html": html,

          
          # "bcc" : 'michelle@firstcodeacademy.com, alan@firstcodeacademy.com',

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





