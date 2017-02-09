from __future__ import unicode_literals

from django.db import models

# Create your models here.
from django.db.models.signals import post_save
from django.utils import timezone
from django.conf import settings
from django.dispatch import receiver
from django.forms import ModelForm
from datetime import datetime
from django.db.models import Count


from datetime import timedelta
import uuid, os

DEFAULT_PROFILE_PICTURE_URL = 'http://placehold.it/350x350'
# from uploadApp.models import language_choices
language_choices = (
  ('', 'None'),
  ('PYTHON', 'Python'),
  ('MINECRAFT', 'Minecraft'),
  ('3DPRINTING', '3DPrinting'),
  ('APPINVENTOR', 'AppInventor'),
  ('SCRATCH', 'Scratch'),
  ('JAVA', 'Java'),
  ('JS', 'JavaScript'),
  ('UNITY', 'Unity'),
  ('MBOT', 'mBot'),
  ('SWIFT', 'Swift'),
  ('HOPSCOTCH', 'Hopscotch'),
  ('ROBOTICS', 'Robotics'),
  ('SCRATCHX', 'ScratchX'),
  ('OTHER', 'Other'),

)

role_UserCourseRelationship_choices = (
    ('S', 'student'),
    ('I', 'instructor'),
)

from django.contrib.postgres.fields import JSONField
from dateutil.parser import parse as dateTimeParse

def codeNinjaCacheData_default():
  return {}

class CodeNinjaCache(models.Model):
  """
  long polling results from code Ninjas endpoint
  """
  endpoint = models.CharField(max_length=500, blank=False)
  lastModified = models.DateTimeField(auto_now= True)
  data = JSONField(default = codeNinjaCacheData_default)

  def getCourseDates(self):
    """
    extracts class dates info from data supplied from code ninja, 
    - http://hk.firstcodeacademy.com/api/camps/:id
      - for camps we will assume that everyday has a class, iterate data to find dates, this will otherwise return blank
    - api/programs
      - extract dates from field "class_dates": 
    """

    if 'api/programs' in self.endpoint:
      # this is a programs endpoint which has a class_dates field in self.data
      cd = self.data.get('class_dates').replace(';\r\n',',').split(',')

      print cd

      # extract year from start_date
      year = dateTimeParse(self.data.get('start_date')).year

      datesMemo = {}

      # parse date string from class_dates
      for dStr in cd:
        try:
          # try to extract dates, which might fail when it reads something like "Lesson 1"
          d = dateTimeParse(dStr)
          d = d.replace(year = year)

          # that's the day of the week, 0 is Monday, 6 is Sunday
          weekday = d.weekday()

          print 'dStr', dStr, 'd', d, 'weekday', weekday

          if weekday not in datesMemo:
            datesMemo[weekday] = []

          datesMemo[weekday].append(d)

        except ValueError as e:
          pass

      return datesMemo






    # return default value
    return []



  class Meta:
    unique_together = ('endpoint',)

def makeEmptyList():
  return []

class UserCourseRelationship(models.Model):
  """
  this takes care of both student enrollment and instructor assignment
  """
  user = models.ForeignKey('profiles.User')
  course = models.ForeignKey('Course')

  role = models.CharField(max_length=1, default='S', choices = role_UserCourseRelationship_choices)

  class Meta:
    unique_together = ('user', 'course',)


formatLocation_choices = {
  'kowloon': 'Unit 404, 4/F, Kowloon Building, 555 Nathan Road, Yau Ma Tei, Hong Kong',
  'sheung wan': 'Unit 302-305, 3/F, Hollywood Centre, 233 Hollywood Road, Sheung Wan, Hong Kong',
}

class Course(models.Model):
  name = models.CharField(max_length=255, blank=False)

  # code Ninja type which tells which endpoint the data came from
  cnType = models.CharField(max_length=255, blank=False, default=None, null=True)
  
  event_type = models.CharField(max_length=255, blank=False, default=None, null=True)


  course_code = models.CharField(max_length=255, blank=False)
  course_icon_url = models.URLField(blank=True, default=DEFAULT_PROFILE_PICTURE_URL)
  eventbrite_tag = models.CharField(max_length=255, blank=True)

  age_group = models.CharField(max_length=255, blank=True)
  location = models.CharField(max_length=255, blank=True)
  start_date = models.DateTimeField(null=True)
  end_date = models.DateTimeField(null=True)
  start_time = models.DateTimeField(null=True)
  end_time = models.DateTimeField(null=True)
  capacity = models.IntegerField(default = 0)
  enrollment_count = models.IntegerField(default = 0)
  active = models.BooleanField(default = True)
  remark = models.TextField(blank=True)

  prices = JSONField(default = makeEmptyList)

  # determine what dates these classes are on, by default they will follow whatever is given by codeninja
  # classDates = JSONField(default = makeEmptyList)

  lastModified = models.DateTimeField(auto_now= True)

  def firstDate(self):
    """
    returns the first date of the course
    """
    d = self.start_date
    if d is not None:
      # example:
      # In [17]: n.strftime('%b %d, %Y')
      # Out[17]: 'Feb 09, 2017'
      return d.strftime('%b %d, %Y')

    # search CourseClassDateRelationship for dates instead.


    # return a default date
    return None

  def firstTime(self):
    """
    returns the first date of the course

    In [38]: dd.strftime('%r')
    Out[38]: '02:57:23 PM'
    """

    d = self.start_time
    if d is not None:
      return d.strftime('%r')

    return None


  def formatLocation(self):
    """
    returns a pretty format of locations 
    """
    return formatLocation_choices.get(self.location, None)


  class Meta:
    # course code must be unique
    unique_together = ('course_code',)

class CourseClassDateRelationship(models.Model):
  course = models.ForeignKey('Course')
  # if classes are bought over but needs to be manually cleaned up, use ignore so dates will not be counted as a classdate
  ignore = models.BooleanField(default=False)
  startDateTime = models.DateTimeField()
  endDateTime = models.DateTimeField()





def awardDefinition_default():
  return {}

def ruleDefinition_default():
  return {
    # 'topic':'Postcard',
    'media':[
      # artwork for this challenge or group of questions
      'https://media.kahoot.it/5e1a14b6-6aa5-4c3c-8ba8-069c4336becd',
      
    ], 
    'questions':[
      {
        'type': 'multipleChoice',
        'answerKey': 'a',
        'question': 'What does the "clear" block do?',
        'media': [
          'https://media.kahoot.it/1f160791-6512-4f8a-af33-5ed49d23711a',
        ],
        'choices': {
          'a':"It clears our app of drawn lines",
          'b':"It doesn't do anything",
          'c':"it clears our variable",
          'd':"It clears our pen color",
        }
      },
      {
        'type': 'multipleChoice',
        'answerKey': 'a',
        'question': 'What is drawSquare?',
        'choices': {
          'a':"A procedure",
          'b':"An event",
          'c':"A loop",
          'd':"A motion block",
        }
      },
      {
        'type': 'multipleChoice',
        'answerKey': 'c',
        'question': 'Why do we turn 90 degrees 4 times?',
        'choices': {
          'a':"We need to turn the right way before pen down",
          'b':"There is no reason",
          'c':"We need ot draw four sides of a square",
          'd':"We need to keep turning forever",
        }
      },
    ]

  }

class Lesson(models.Model):
  name = models.CharField(max_length=255, blank=False)
  order = models.IntegerField(blank = False, default = 0)
  course = models.ForeignKey('Course')

  class Meta:
    # same lesson under course can only occur once
    unique_together = ('name', 'course',)


class Challenge(models.Model):
  name = models.CharField(max_length=255, blank=False)
  # newcomers quiz
  order = models.IntegerField(blank = True, default = 0)
  createdDate = models.DateTimeField(default=timezone.now)

  lesson = models.ForeignKey('Lesson', blank=True, null=True, default=None)



  # ruleDefinition: will determine what kind of challenges will load
  ruleDefinition = JSONField(default = ruleDefinition_default)

  # {
  # 	'type': 'multipleChoice'
  # 	'question': 'What is our company name?'
  # 	'topic': 'randomness',

  # 	'foo': 'bar',

  # 	'choices': [
  # 	'first code academy',
  # 	'second code academy',
  # 	'something',
  # 	]
  # 	'answer:'


  # }

  # this determines what kind of awards are given when challenge is completed
  # there is a chance that completing a challenge yields multiple challenge records
  # awardDefinition = JSONField(default = awardDefinition_default, null=True,)

  # each challenge when completed results in a ChallengeRecord, to mark that the challenge is completed
  # point = models.IntegerField(blank = False, default = 10)

class ChallengeProgress(models.Model):
  challenge = models.ForeignKey('Challenge')
  user = models.ForeignKey('profiles.User')
  # just to store some MD5 hash to signify progress in a challenge
  signature = models.CharField(max_length=32, blank=False)

  class Meta:
    # same progress can only occur once
    unique_together = ('user', 'challenge', 'signature')


DEFAULT_TROPHY_PICTURE_URL = 'https://s3-ap-southeast-1.amazonaws.com/fcanectar/customMedia/trophIcon.png'

class Trophy(models.Model):
  name = models.CharField(max_length=255, blank=False)
  avatar_url = models.URLField('avatar_url',blank=True, default=DEFAULT_TROPHY_PICTURE_URL)

  # describes how many points are required to attain trophy
  threshold = models.IntegerField(blank = False, default = 100)

  language = models.CharField( max_length=20, default='', choices = language_choices)

  description = models.TextField(blank=True)

  def __unicode__(self):
        return unicode(self.name)


class ChallengeRecord(models.Model):
  """ 
  this is where students record their points for challenges, each challenge has to work towards some trophy
  """
  createdDate = models.DateTimeField(default=timezone.now)

  trophy = models.ForeignKey('trophy',null = True)
  user = models.ForeignKey('profiles.User')
  point = models.IntegerField(blank = False, default = 10)

  # record challenges with record so no challenges may be repeated,
  # retain null = true to accomodate upload scenarios
  challenge = models.ForeignKey('challenge',null = True)



class TrophyRecord(models.Model):
  """ 
  when students accumulate challenge points and cross a trophy's threshold, they win a trophy, each user can only win a trophy once
  """
  createdDate = models.DateTimeField(default=timezone.now)
  trophy = models.ForeignKey('trophy')
  user = models.ForeignKey('profiles.User')

  def __unicode__(self):
        return unicode(self.trophy.name)

  class Meta:
    unique_together = ('user', 'trophy',)










