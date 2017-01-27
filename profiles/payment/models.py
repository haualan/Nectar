# payment / accounting related models live here
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


from datetime import timedelta
import dateutil.parser
import uuid, os

from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

import stripe

from django.contrib.postgres.fields import JSONField

from django.db import transaction





class Coupon(models.Model):
  """
  keeps all valid coupons in the system, 
  must be careful not to expose any on endpoints and that only validations are allowed
  """

  # unique coupon codes are enforced
  code = models.CharField(max_length=255, blank=False, null=False, unique=True)

  description_public = models.TextField(blank=True)
  description_internal = models.TextField(blank=True)

  # effectDollar is the dollar amount it takes off the charge
  effectDollar = models.DecimalField(max_digits=9, decimal_places=6, default=0)

  # effectMultiplier is the multiplier applied for the discount (.95) implies 5% off
  effectMultiplier = models.DecimalField(max_digits=9, decimal_places=6, default=1.00)

  lastModified = models.DateTimeField(auto_now=True)

  # coupon may be set to have no end date
  validFrom = models.DateTimeField(default=timezone.now, null=True)
  validTo = models.DateTimeField(default=None, null=True)


  # optional fun things to do with coupons
  # optional timer 
  timerSeconds = models.IntegerField(default = None, null=True)

  maxUses = models.IntegerField(default = None, null=True)

  # if true, then coupon can be used for any products / like a general discount for everything
  isValidForAll = models.BooleanField(default = False)


class CouponCourseRelation(models.Model):
  """
  assigns relationship of coupons and the courses they are valid on
  """
  coupon = models.ForeignKey('Coupon')
  course = models.ForeignKey('course.Course')

  class Meta:
    # the same coupon must only be associated to the same course once 
    unique_together = ('coupon', 'course')





class CouponUserRelation(models.Model):
  """
  applies coupon to a user
  transaction amount must be determined by the server to avoid overrides on client side right before transaction
  - coupons may be used multiple times but may not stack towards the same transaction

  """

  user = models.ForeignKey('User')

  # creation timestamp
  timestamp = models.DateTimeField(auto_now_add=True)

  coupon = models.ForeignKey('Coupon')

  isUsed = models.BooleanField(default = False)

  @transaction.atomic
  def save(self, *args, **kwargs):
    # there can be multiple used coupons (isUsed = True) for a paying user but only one active coupon (isUsed = False)
    if not self.isUsed:
      CouponUserRelation.objects.filter(
        user = self.user,
        coupon = self.coupon,
        isUsed = False
      ).update(isUsed= True)

    super(CouponUserRelation, self).save(*args, **kwargs)

event_type_choices = (
  ('charge.succeeded', 'charge.succeeded'),
  ('charge.refunded', 'charge.refunded'),
)

class Ledger(models.Model):
  """
  this houses all the transactions made for purchases and refunds and also supports manual transactions
  """
  # rawData contains the entire payload from stripe (payment processor)
  rawData = JSONField(null=True)

  # unique identifier for the generated event, it may be blank in the event that the event is manually created
  event_id = models.CharField(max_length=255, blank=False, null=True, unique=True)
  event_type = models.CharField(max_length=255, blank=False, choices = event_type_choices)

  amount = models.IntegerField(default= 0)
  amount_refunded = models.IntegerField(default = 0)

  livemode = models.BooleanField(default = False)
  transactionDateTime = models.DateTimeField(default=timezone.now)
  currency = models.CharField(max_length=3, blank=False,)

  # so we can relate dataset to the user this is applied on
  stripeCustomerId = models.CharField(max_length=255, null=True,)

  # this should usually be supplied by stripe in the metadata field, 
  # but not a strict tie with User foreign key because we want the ledger to persist no matter what
  # consider the cases where course codes or users are deleted
  buyerID = models.CharField(max_length=255, null=False,)
  studentID = models.CharField(max_length=255, null=False,)
  course_code = models.CharField(max_length=255, null=False,)







