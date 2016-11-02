from __future__ import absolute_import


import os, urllib

from celery import Celery
from .celeryconfig import *

# remember to run on target machine after every restart:
# export PYTHONPATH=$PYTHONPATH:$PWD

# to start local worker on debug, go to directory of project (where manage.py lives):
# celery -A SixCycle worker --loglevel=info

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Nectar.settings')
import django
django.setup()



# from django.conf import settings  # noqa



# AWS_ACCESS_KEY_ID = 'AKIAILZTRD2QXRUSKYXQ'
# AWS_SECRET_ACCESS_KEY = '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'
# BROKER_URL = 'sqs://{}:{}@'.format(AWS_ACCESS_KEY_ID, urllib.quote_plus(AWS_SECRET_ACCESS_KEY))
# BROKER_TRANSPORT_OPTIONS = {
#   'region': 'us-east-1',
#   'visibility_timeout': 30,
#   'polling_interval': 10,
#   'queue_name_prefix': CELERY_Q_NAME_PREFIX,
#   }


app = Celery('Nectar')


# app.conf.CELERY_TASK_SERIALIZER = 'json'


app.conf.update(
  CELERY_TASK_SERIALIZER='json',
  BROKER_URL = BROKER_URL,
  BROKER_TRANSPORT_OPTIONS = BROKER_TRANSPORT_OPTIONS,
)

@app.task(name='activities.tasks.add')
def testadd(x,y):
  print('defered testadd')

# @app.task(name='activities.tasks.processStravaImport')
# def delay_processStravaImport(payload):
#   print('sending defered celery processStravaImport... {}'.format(payload))


@app.task(bind=True)
def debug_task(self):
  print('Request: {0!r}'.format(self.request))

# Using a string here means the worker will not have to
# pickle the object when using Windows.
# app.config_from_object('django.conf:settings')
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)



# define all tasks to be sent by the server above before importing tasks below
# from activities.tasks import *






# from celery import Celery, shared_task
# # from django.conf import settings
# import urllib

# # settings.configure()
# AWS_ACCESS_KEY_ID = 'AKIAILZTRD2QXRUSKYXQ'
# AWS_SECRET_ACCESS_KEY = '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'
# BROKER_URL = 'sqs://{}:{}@'.format(AWS_ACCESS_KEY_ID, urllib.quote_plus(AWS_SECRET_ACCESS_KEY))
# BROKER_TRANSPORT_OPTIONS = {
#   'region': 'us-east-1',
#   'visibility_timeout': 30,
#   'polling_interval': 10,
#   'queue_name_prefix': 'celery-',
#   }

# CELERY_RESULT_BACKEND = 'redis://sc-redis.olfidd.0001.use1.cache.amazonaws.com:6379/0'


# # app = Celery('tasks', broker=settings.BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)

# app = Celery('tasks', broker=BROKER_URL, backend=CELERY_RESULT_BACKEND)


# # all the tasks are here
# @app.task(name='activities.utilsToolbox.distWorkers.add')
# def adds(x, y):
#   return x + y

# # # calling the task above
# # add.delay(4, 4)

