import urllib
from config import AWS_ACCESS_KEY_ID , AWS_SECRET_ACCESS_KEY , CELERY_Q_NAME_PREFIX, AWS_DEFAULT_REGION

# set these keys in the os env
import os
os.environ.setdefault('AWS_ACCESS_KEY_ID', AWS_ACCESS_KEY_ID)
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', AWS_SECRET_ACCESS_KEY)
os.environ.setdefault('AWS_DEFAULT_REGION', AWS_DEFAULT_REGION)


# Django Celery Settings
BROKER_URL = 'sqs://{}:{}@'.format(AWS_ACCESS_KEY_ID, urllib.quote_plus(AWS_SECRET_ACCESS_KEY))
BROKER_TRANSPORT_OPTIONS = {
  'region': 'us-east-1',
  'visibility_timeout': 30,
  'polling_interval': 10,
  'queue_name_prefix': CELERY_Q_NAME_PREFIX,
  }

CELERY_RESULT_BACKEND = 'redis://sc-redis.olfidd.0001.use1.cache.amazonaws.com:6379/0'

