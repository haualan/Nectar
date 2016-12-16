from __future__ import unicode_literals

from django.db import models

# Create your models here.
from django.db.models.signals import post_save
from django.utils import timezone
from django.conf import settings
from django.dispatch import receiver
from django.forms import ModelForm
from django.db.models import Count

import dateutil.parser
import uuid, os

DEFAULT_PROFILE_PICTURE_URL = 'http://placehold.it/350x350'

action_choices = (
	(0, 'Love'),
    (1, 'Like'),
    (2, 'Wow'),
)


class TrophyRecordAction(models.Model):
  """
  each trophy record can be loved by a user
  """
  user = models.ForeignKey('profiles.User')
  trophyRecord = models.ForeignKey('course.TrophyRecord')
  action = models.IntegerField(default=0, choices = action_choices)


  class Meta:
  	# each user can only love an item once
    unique_together = ('user', 'trophyRecord', 'action')


class ProjectAction(models.Model):
  """
  each project / uploaded app can be loved by a user
  """
  user = models.ForeignKey('profiles.User')
  project = models.ForeignKey('uploadApp.Project')
  action = models.IntegerField(default=0, choices = action_choices)

  class Meta:
    # each user can only love an item once
    unique_together = ('user', 'project', 'action')


# may not be necessary, just have the trophies be linked to challenges may be more approps

# class ChallengeAction(models.Model):
#   """
#   each project / uploaded app can be loved by a user
#   """
#   user = models.ForeignKey('profiles.User')
#   project = models.ForeignKey('uploadApp.Project')
#   action = models.IntegerField(default=0, choices = action_choices)

#   class Meta:
#     # each user can only love an item once
#     unique_together = ('user', 'project', 'action')










