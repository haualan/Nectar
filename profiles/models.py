from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
from django.conf import settings
from django.dispatch import receiver
from django.forms import ModelForm
from datetime import datetime
from django.db.models import Count

from rest_framework.authtoken.models import Token
from authtools.models import AbstractEmailUser


from jsonfield import JSONField
from datetime import timedelta
import dateutil.parser

# from activities.statistics.heartratemodel.utils import *
# from activities.statistics.jackdaniels import calc_JD_pace_heartrate


gender_choices = (
      ('M', 'male'),
      ('F', 'female'),
  )

import pytz
tzName_choices = set((i, i) for i in pytz.all_timezones)

def get_eighteen_yearoldDate():
  return datetime((timezone.now().year - 18), 1, 1)

def get_default_age():
  return datetime((timezone.now().year - 30), 1, 1)

DEFAULT_PROFILE_PICTURE_URL = 'http://placehold.it/350x350'

class User(AbstractEmailUser):
  profile_picture_url = models.URLField('profile_picture_url',blank=True, default=DEFAULT_PROFILE_PICTURE_URL)
  birth_date = models.DateField('birth_date', blank=True, default=get_default_age)
  gender = models.CharField('gender', max_length=1, default='M', choices = gender_choices)
  name = models.CharField('name', max_length=255, blank=True)
  height_in_meters = models.FloatField('height_in_meters', default=1.60)
  weight_in_kg = models.FloatField('weight_in_kg', default= 70.0)
  is_group_activity_anon = models.BooleanField('is_group_activity_anon', default = True)
  username = models.CharField('username', max_length=255, blank=True)

  login_log = JSONField(default = "[]")
  # timezone offset relative to UTC
  tzName = models.CharField(max_length=100, default = 'America/New_York',  choices = tzName_choices)
  phoneNumber = models.CharField(max_length=50, blank=True, null=True)
  location = models.CharField(max_length=100, blank=True, null=True)
  isSearchable = models.BooleanField(default = True)

  # controls whether email notifications are sent.
  isEmailNotified = models.BooleanField(default = True)

  # controls whether paywall is active for user
  showPayWall = models.BooleanField(default = False)


  def save(self, *args, **kwargs):
    # truncate any query params on the url @jon issue with s3 temporary validation links 02/27/2016
    # try:
    #   self.profile_picture_url = self.profile_picture_url.split('?')[0]
    # except:
    #   pass

    super(User, self).save(*args, **kwargs) # Call the "real" save() method.
  
  # @classmethod
  # def truncate_urls(cls):
  #   users = cls.objects.all()
  #   for u in users:
  #     u.save()



  def get_profile_picture_url_for_email(self):
    """
    @alan, as per @kristo provide user image for email purpose but return None if it is using the default
    """
    if DEFAULT_PROFILE_PICTURE_URL == self.profile_picture_url:
      return None
    return self.profile_picture_url

  def get_age(self):
    today = datetime.now()
    return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

  def get_full_name(self):
    return self.name

  # @new-thread
  def record_login(self):
    """
    used to record a user's logging in
    """
    # print 'self.login_log', self.login_log , type(self.login_log)
    nd = timezone.now().date()
    if not isinstance(self.login_log, list):
      print 'self.login_log is str'
      self.login_log = []

    # exit function if date is repeated
    # if format(nd) in self.login_log:
    #   return False

    # clean up old logins
    cuttoff = timezone.now().date() - timedelta(14)

    for i, v in enumerate(self.login_log):
      try:
        if dateutil.parser.parse(v).date() < cuttoff:
          self.login_log.pop(i)
      except:
        self.login_log.pop(i)

    self.login_log.append(nd)
    self.login_log = list(set(self.login_log))
    self.save()

  # def get_defaultPlan(self):
  #   isGroup = False
  #   planId = None

  #   g_list = self.GroupMemberRelation.values('group').annotate(Count('group__GroupPlanCalendar__GroupCycleCalendar')).filter(
  #               group__GroupPlanCalendar__GroupCycleCalendar__count__gt = 0,
  #               is_admin = False)
  #   g_list = [i['group'] for i in g_list ]

  #   if len(g_list) > 0:
  #     return {
  #       'isGroup': True
  #       'planId': g_list[0]['group']
  #     }

  #   return {
  #     'isGroup': False,
  #     'planId': None
  #   }


  def __unicode__(self):              
    return self.email

class UserForm(ModelForm):
  """
  This is the form fields showing fields a user is allowed to change
  """
  class Meta:
    model = User
    fields = ['email', 'username', 'name', 'profile_picture_url', 'birth_date', 'gender', 'height_in_meters', 'isSearchable']
