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
import dateutil.parser
import uuid, os

import nltk

class Marketing(models.Model):
  """
  this takes care of both student enrollment and instructor assignment
  """
  year = models.IntegerField(default=None, null=True)

  eventType = models.CharField(max_length=50, default=None, null=True)
  batch = models.CharField(max_length=50, default=None, null=True)
  period = models.CharField(max_length=50, default=None, null=True)
  cohort = models.CharField(max_length=50, default=None, null=True)
  course = models.CharField(max_length=100, default=None, null=True)
  firstName = models.CharField(max_length=100, default=None, null=True)
  lastName = models.CharField(max_length=100, default=None, null=True)

  # poor formating exists
  birthDate = models.CharField(max_length=20, default=None, null=True)
  age = models.IntegerField(default=None, null=True)
  gender = models.CharField(max_length=10, default=None, null=True)
  school = models.CharField(max_length=100, default=None, null=True)
  grade = models.CharField(max_length=50, default=None, null=True)
  parentFirstName = models.CharField(max_length=100, default=None, null=True)
  parentLastName = models.CharField(max_length=100, default=None, null=True)

  # sometimes multiple emails are in here
  parentEmail = models.CharField(max_length=200, default=None, null=True)
  parentMobile = models.CharField(max_length=50, default=None, null=True)
  homeAddress = models.CharField(max_length=500, default=None, null=True)

  # supposed to be number but filled with poor formats
  paid = models.CharField(max_length=50, default=None, null=True)
  promoCode = models.CharField(max_length=50, default=None, null=True)

  # enrollmentDate = models.DateField(default=None, null=True)
  enrollmentDate = models.CharField(max_length=20, default=None, null=True)


  howHeard = models.CharField(max_length=50, default=None, null=True)
  comments = models.CharField(max_length=500, default=None, null=True)
  eventbriteEventID = models.CharField(max_length=50, default=None, null=True)
  eventbriteOrderID = models.CharField(max_length=50, default=None, null=True)
  eventBriteOrderDate = models.CharField(max_length=50, default=None, null=True)
  classLocation = models.CharField(max_length=50, default=None, null=True)

  guessSchool = models.CharField(max_length=50, default=None, null=True)

  def cleanSchool(self, validSchoolsList=[]):
    """
    takes real school model and tries to map them to this messy db
    """
    
    # given a valid school list, compute edit distance 
    validSchoolsScores = [(schoolName , nltk.edit_distance(schoolName, self.school  ) ) for schoolName in validSchoolsList ]

    # sort the scores
    validSchoolsScores.sort(key=lambda x: x[0])

    print 'validSchoolsScores'
    print validSchoolsScores
    # pick the top 5


    # give user choice to assign

    pass
