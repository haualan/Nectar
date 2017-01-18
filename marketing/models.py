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

  def cleanSchool(self, validSchoolsList=None):
    """
    takes real school model and tries to map them to this messy db
    """

    if validSchoolsList is None:
      validSchoolsList = [ i['name'] for i in School.objects.all().values('name')]

    
    # given a valid school list, compute edit distance 
    validSchoolsScores = [(schoolName , nltk.edit_distance(schoolName, self.school  ) ) for schoolName in validSchoolsList ]

    # sort the scores
    validSchoolsScores.sort(key=lambda x: x[1])

    print 'cleanSchool info for data id:', self.id, 
    print 'original school input:', self.school
    print '1: ', validSchoolsScores[0]
    print '2: ', validSchoolsScores[1]
    print '3: ', validSchoolsScores[2]
    print '4: ', validSchoolsScores[3]
    print '5: ', validSchoolsScores[4]
    print '\n'
    print '0: ', 'Other'




    # pick the top 5


    # give user choice to assign
    choice = None

    validChoices = (0,1,2,3,4,5)

    while choice not in validChoices:
      if choice is not None:
        print choice, 'is not a valid entry.'
      choice = raw_input("Please enter a choice: ")
      print "you entered", choice

    if choice == 0:
      self.guessSchool = None
      return self.save()

    self.guessSchool = validSchoolsScores[choice  - 1][0]
    return self.save()

    # return validSchoolsScores
