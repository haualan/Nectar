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

from rest_framework.exceptions import APIException, ParseError, PermissionDenied






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
  effectDollar = models.DecimalField(max_digits=15, decimal_places=6, default=0)

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


currencyMultiplier = {
  # because stripe uses 100 as 1 dollar
  'hkd': 0.01,
  'sgd': 0.01,
  'twd': 0.01,
}

source_choices = (
  ('CC', 'credit card'),
  ('CASH', 'cash'),
  ('CHECK', 'check'),
  ('OTHER', 'other'),
)


from django.contrib.auth import get_user_model
UserModel = get_user_model()

from Course.models import Course

class Ledger(models.Model):
  """
  this houses all the transactions made for purchases and refunds and also supports manual transactions
  """
  # rawData contains the entire payload from stripe (payment processor)
  rawData = JSONField(null=True)

  # unique identifier for the generated event, it may be blank in the event that the event is manually created
  event_id = models.CharField(max_length=255, blank=False, null=True, unique=True)
  event_type = models.CharField(max_length=255, blank=False, choices = event_type_choices)

  # unreliable fields for accounting purposes
  # amount = models.IntegerField(default= 0)
  # amount_refunded = models.IntegerField(default = 0)

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


  # order_id is the tax lot opening transaction, refunds should be deducted against this id
  order_id = models.CharField(max_length=255, null=True,)

  # if positive, indicates money charged, if negative, indicates refunds
  localCurrencyChargedAmount = models.DecimalField(max_digits=15, decimal_places=6, default=0)


  # check who is this transaction entered by, could be None on DB, or uid
  signBy = models.CharField(max_length=255, blank=False, null=True)

  # what kind of transaction is this? cc, cash , check, 
  source = models.CharField(max_length=10, blank=False, choices = source_choices)

  # special remarks for this order for ops staff
  remarks = models.TextField(blank=True)


  @transaction.atomic
  def save(self, *args, **kwargs):
    # extract the required data from rawData as provided from stripe
    self.processRawData()

    
    super(Ledger, self).save(*args, **kwargs)

  @classmethod
  def createManualCharge(cls, currency, localCurrencyChargedAmount, buyerID, studentID, course_code, source, user=None, remarks = ""):
    """
    method to create a manual charge, which is an open tax lot, user is the employee_id authorizing this transaction
    """

    # employee must be supplied
    if user is None or user.role not in ('I', 'O', 'C'):
      raise ParseError('Authorized User does not exist')

    # verify if these buyers and students exist, we do not foreign key them 
    # because we do not want django to delete transactions when user objects are deleted by system
    if not UserModel.objects.filter(id = buyerID).exists():
      raise ParseError('buyerID does not exist')

    if not UserModel.objects.filter(id = studentID).exists():
      raise ParseError('studentID does not exist')


    # verify that course_code exists
    if not Course.objects.filter(course_code = course_code).exists():
      raise ParseError('course_code does not exist')


    openTrans = cls.objects.create(
      event_type = 'charge.succeeded',
      event_id = 'evt_man_{}'.format(uuid.uuid4()),
      order_id = 'ch_{}_{}'.format(user.id, uuid.uuid4()),

      signBy = user.id,
      currency = currency,
      localCurrencyChargedAmount = localCurrencyChargedAmount,
      buyerID = buyerID,
      studentID = studentID,
      course_code = course_code,
      source = source,
      remarks = remarks,


      livemode= True,



    )
    return openTrans

  @classmethod
  def createManualRefund(cls, localCurrencyChargedAmount, order_id, source, user=None, remarks = "" ):
    """
    given the order ID of the opening taxlot, apply a refund
    """

    if user is None or user.role not in ('I', 'O', 'C'):
      raise ParseError('Authorized User does not exist')

    # this is the opening tax lot, check for existence first
    openTrans = cls.objects.filter(order_id=order_id)
    if not openTrans and order_id is not None:
      raise ParseError('order_id does not exist')

    openTrans = openTrans.first()


    # many attributes of openTrans will be reused
    newRefund = cls.objects.create(

      event_type = 'charge.refunded',
      event_id = 'evt_man_{}'.format(uuid.uuid4()),

      # order_id from the originating tax lot
      order_id = openTrans.order_id,

      signBy = user.id,
      currency = openTrans.currency,
      localCurrencyChargedAmount = localCurrencyChargedAmount,
      buyerID = openTrans.buyerID,
      studentID = openTrans.studentID,
      course_code = openTrans.course_code,
      source = source,
      remarks = remarks,


      livemode= openTrans.livemode,


    )



    return newRefund

  def extractLocalCurrencyChargedAmount(self):
    """
    extracts the transaction amount <number> given the raw data from stripe
    - positive if it is a charge against the customer
    - negative if it is a refund
    """

    dataWrapper = self.rawData
    obj = dataWrapper['data']['object']

    event_type = dataWrapper['type']

    # init default returns
    transactionDateTime = timezone.make_aware(timezone.datetime.fromtimestamp(obj['created']))
    localCurrencyChargedAmount = 0


    if event_type == 'charge.succeeded':
      # if it's a charge, that's similar to opening a tax lot, an the transaction is a positive number
      localCurrencyChargedAmount = obj['amount'] * currencyMultiplier[self.currency]
      return localCurrencyChargedAmount , transactionDateTime

    if event_type == 'charge.refunded':
      # if it's a refund, one must traverse through the list of refunds to find how much this refund has been made

      refundList = obj['refunds']['data']
      

      # assume the first object in this list is the refunded amt.
      if len(refundList) > 0:
        refund = refundList[0]
        # negative amount for a refund
        localCurrencyChargedAmount = refund.get('amount') * currencyMultiplier[self.currency] * -1
        transactionDateTime = timezone.make_aware(timezone.datetime.fromtimestamp(refund.get('created')))

      return localCurrencyChargedAmount , transactionDateTime 
      

    # this returns the default values
    return localCurrencyChargedAmount , transactionDateTime 



  def processRawData(self):
    """
    given a payload from stripe, extract details and add contents back into ledger
    """
    if self.rawData is None:
      # do nothing if no rawData
      return


    # signify that raw data comes from stripe
    self.signBy = 'Stripe'

    dataWrapper = self.rawData
    obj = dataWrapper['data']['object']

    event_type = dataWrapper['type']
    event_id = dataWrapper['id']

    livemode = dataWrapper['livemode']
    

    currency = obj['currency']

    # these fields are not reliable for accounting purposes
    # amount = obj['amount']
    # amount_refunded = obj['amount_refunded']
    
    stripeCustomerId = obj['customer']
    order_id = obj['id']

    # so we can relate dataset to the user this is applied on
    metadata = obj['metadata']
    buyerID = None
    if 'buyerID' in metadata:
      buyerID = metadata['buyerID']

    studentID = None
    if 'studentID' in metadata:
      studentID = metadata['studentID']


    course_code = None
    if 'course_code' in metadata:
      course_code = metadata['course_code']


    self.livemode = livemode
    self.currency = currency
    # amount = amount,
    # amount_refunded = amount_refunded,
    self.buyerID = buyerID
    self.studentID = studentID
    self.course_code = course_code
    self.stripeCustomerId = stripeCustomerId
    self.order_id = order_id


    # assume all stripe charges are. cc
    self.source = 'CC'

    # has to be at the bottom, requires other precalculated data at the top
    self.localCurrencyChargedAmount, self.transactionDateTime = self.extractLocalCurrencyChargedAmount()




