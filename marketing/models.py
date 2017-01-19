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

from profiles.models import School


from datetime import timedelta
import dateutil.parser
import uuid, os

import nltk


class StudentDump(models.Model):
  """
  temp dump of students
  """
  fullName = models.CharField(max_length=200, default=None, null=True)
  # poor formating exists
  school = models.CharField(max_length=100, default=None, null=True)
  email = models.CharField(max_length=200, default=None, null=True)


class EventbriteDump(models.Model):
  """
  temp dump of students
  """
  fullName = models.CharField(max_length=200, default=None, null=True)
  # poor formating exists
  school = models.CharField(max_length=100, default=None, null=True)



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

  autoGuessSchool = models.CharField(max_length=50, default=None, null=True)

  def autoCleanSchool(self, validSchoolsList=None):
    """
    same as clean school but have the computer just auto pick the best choice
    """

    return self.cleanSchool(validSchoolsList, auto=True)


  def cleanSchool(self, validSchoolsList=None, auto=False):
    """
    takes real school model and tries to map them to this messy db
mm = Marketing.objects.all().first()
mm.cleanSchool()

    """

    if validSchoolsList is None:
      validSchoolsList = [ i['name'] for i in School.objects.all().values('name')]

    if self.school is None:
      print 'None in original data can only be skipped'
      return 


    # given a valid school list, compute edit distance 
    validSchoolsScores = [(schoolName , nltk.edit_distance(schoolName, self.school  ) ) for schoolName in validSchoolsList ]

    # sort the scores
    validSchoolsScores.sort(key=lambda x: x[1])

    # if auto were true, choose the best
    if auto:
      schoolChoice = validSchoolsScores[0][0]
      print 'Auto Assigned:', validSchoolsScores[0], 'mapped to', self.school
      self.autoGuessSchool = schoolChoice
      return self.save()


    
    print 'cleanSchool info for data id:', self.id, 
    print '\n'
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

    validChoices = ("0","1","2","3","4","5")

    while choice not in validChoices:
      if choice is not None:
        print choice, 'is not a valid entry.'
      choice = raw_input("Please enter a choice: ")

      # take out newline
      # choice = choice[:-1]

      print "you entered", choice

    if int(choice) == 0:
      self.guessSchool = None
      print 'Assigned Other / None'
      return self.save()

    schoolChoice = validSchoolsScores[int(choice)  - 1][0]
    print 'Assigned:', schoolChoice
    self.guessSchool = schoolChoice
    return self.save()

    # return validSchoolsScores
