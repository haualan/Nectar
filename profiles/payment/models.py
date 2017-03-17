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
from django.forms.models import model_to_dict

from rest_framework.exceptions import APIException, ParseError, PermissionDenied

from profiles.models import User






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


currencyInferTz = {
  'hkd': timezone.pytz.timezone("Asia/Hong_Kong"),
  'sgd': timezone.pytz.timezone("Asia/Singapore"),
  'twd': timezone.pytz.timezone("Asia/Taipei"),
}

source_choices = (
  ('CC', 'credit card'),
  ('CASH', 'cash'),
  ('CHECK', 'check'),
  ('OTHER', 'other'),
)


# from django.contrib.auth import get_user_model
# UserModel = get_user_model()

from profiles.models import User
UserModel = User


from course.models import Course


stripeAcct_choices = [ (k, k) for k in settings.STRIPE_SECRET_MAP]

class Ledger(models.Model):
  """
  this houses all the transactions made for purchases and refunds and also supports manual transactions
  """
  # rawData contains the entire payload from stripe (payment processor)
  rawData = JSONField(null=True)

  # unique identifier for the generated event, it may be blank in the event that the event is manually created
  event_id = models.CharField(max_length=255, blank=False, null=True)
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
  source = models.CharField(max_length=10, blank=False, choices = source_choices, default='OTHER')

  # special remarks for this order for ops staff
  remarks = models.TextField(blank=True)

  # which stripe acct processed this, use contents to lookup stripe key in conifg
  stripeAcct = models.CharField(max_length=30, blank=False, null=True, choices=stripeAcct_choices)


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

  def formatPriceStr(self):
    """
    returns a pretty formatted string for prices
    """
    return '{} {}'.format(int(self.localCurrencyChargedAmount), self.currency.upper())

  def getBuyerUser(self):
    """
    returns the buyer user else none
    """

    buyerUser = UserModel.objects.filter(id = self.buyerID)
    if buyerUser:
      return buyerUser.first()

    return None

  def getStudentUser(self):
    """
    returns the student user else none
    """

    studentUser = UserModel.objects.filter(id = self.studentID)
    if studentUser:
      return studentUser.first()

    return None

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

  def localizedTransactionDateTime(self):
    """
    given currency, guess the local datetime from utc time
    """

    tzLocal = currencyInferTz.get(self.currency.lower(), None)

    if tzLocal is None:
      return self.transactionDateTime

    return tzLocal.normalize(self.transactionDateTime)

  def formatLocalizedTransactionDateTime(self):
    """
    given currency, guess the local datetime from utc time
    pretty version, date only
    """

    return self.localizedTransactionDateTime().strftime('%b %d, %Y')

  def getCourseOrNone(self):
    """
    returns the course object of the class, or returns none if none found
    """

    c = Course.objects.filter( course_code = self.course_code)
    if c:
      return c.first()

    return None

  @classmethod
  def getRevenueSchedule(cls, startDate=timezone.datetime.min , endDate=timezone.datetime.max):
    """
    show the revenue from our books
    revenue report with course name + course code + courseType (term/camp/event) + parent info + 
    payment amount + service fee + location of class + course start date + course end date + subdomain


    """

    endDate = endDate.replace(hour = 23, minute=59, second = 59, microsecond=999999)

    tzLookup = { k: timezone.pytz.timezone(v.get('tzName'))  for k, v in settings.SUBDOMAINSPECIFICMAPPING.iteritems() }

    defaultTZ = tzLookup.get('hk')
    

    allOrders = cls.objects.filter(
      livemode = True,
      transactionDateTime__gte = startDate, 
      transactionDateTime__lte = endDate
    )

    # list of course_codes from Ledger
    course_codes_set = set([order.course_code for order in allOrders])
    buyerID_set = set([order.buyerID for order in allOrders])

    allCourses = Course.objects.filter(course_code__in = course_codes_set)
    allBuyers = User.objects.filter(id__in = buyerID_set)

    # use this to lookup course info and buyers
    allCourses_dict = { c.course_code : model_to_dict(c) for c in allCourses}
    allBuyers_dict = { u.id : model_to_dict(u) for u in allBuyers}

    # print 'allCourses_dict', allCourses_dict
    # print 'allBuyers_dict', allBuyers_dict


    # fees lookup from stripe, there will be fees per stripe acct in subdomains

    # pad the dates, because not sure when the created dates of these stripe objects match the transactions, what if they don't?
    stripe_startDate = timezone.datetime.min
    if startDate > timezone.datetime.min + timezone.timedelta(days = 3):
      stripe_startDate = startDate - timezone.timedelta(days = 3)

    stripe_endDate = timezone.datetime.max
    if endDate < timezone.datetime.max - timezone.timedelta(days = 3):
      stripe_endDate = endDate + timezone.timedelta(days = 3)

    print 'stripe_startDate', stripe_startDate, 'stripe_endDate', stripe_endDate

    # for each stripe acct in system we attempt to match the fees,
    # non-live transactions will always have 0 fees
    fees_lookup_by_currency = {}
    for k, v in settings.STRIPE_SECRET_MAP_LIVE.iteritems():
      stripe.api_key = v
      bt = stripe.BalanceTransaction.all(
        created = {
          'gt': stripe_startDate,
          'lt': stripe_endDate,
        }
      )
      fees_lookup_by_currency[k] = { 
        i.get('id'): i for i in bt.get('data') if i.get('id', None) and i.get('fee_details', None)
      }


    def lookupFees(l):
      """
      l is the ledger object, filter through currency and txn id to find the fee, 
      fill with 0 for fees not found
      """

      source = l.source

      if source != 'CC':
        # there is fee only for Credit Card / CC transactions
        return 0.0

      currency = l.currency

      txn_id = l.rawData.get(
        'data', {}
      ).get(
        'object', {}
      ).get(
        'balance_transaction', None
      )

      if not currency or not txn_id:
        # missing other info return no fees
        return 0.0

      if not l.livemode:
        # only live mode has real fees / test transactions have nothing
        return 0.0

      print 'lookup fees', txn_id, fees_lookup_by_currency.get(
        currency, {}).get(
        txn_id, {})
      # retreive balance transaction obj from lookup, use 0.0 as a fallback
      return fees_lookup_by_currency.get(
        currency, {}).get(
        txn_id, {}).get(
        'data', {}).get(
        'fee', 0.0)
    
    def getTZstrbySubdomain(l):
      """
      given ledger object, extract timezone info, pad with HKT if not available
      """
      subdomain = allCourses_dict.get(l.course_code, {}).get('subdomain', None)

      if not subdomain:
        return defaultTZ

      return tzLookup.get(subdomain)


    for i in allOrders:
      print 'i.course_code', i.course_code
      print 'i.buyerID', i.buyerID
      print 'subdomain', allCourses_dict.get(i.course_code, {}).get('subdomain', None)
      print 'txn_id', i.rawData.get(
        'data', {}
      ).get(
        'object', {}
      ).get(
        'balance_transaction', None
      )
      print ''


    # build results
    r = []
    for i in allOrders:
      r.append(
        {

        'acctEvent_id': i.event_id,
        'acctTransactionDateTimeUTC': i.transactionDateTime,
        'acctTransactionDateTimeLocal': i.transactionDateTime.astimezone( getTZstrbySubdomain(i) ),
        'acctSource': i.source,
        'acctLocalCurrencyChargedAmount': i.localCurrencyChargedAmount,
        'acctCurrency': i.currency,
        'acctLocalCurrencyServiceFee': lookupFees(i),

        # courseInfo
        'courseLocation': allCourses_dict.get(i.course_code, {}).get('formatLocation', None),
        'courseStartDate': allCourses_dict.get(i.course_code, {}).get('start_date', None),
        'courseEndDate': allCourses_dict.get(i.course_code, {}).get('end_date', None),
        'courseSubdomain': allCourses_dict.get(i.course_code, {}).get('subdomain', None),

        # parentInfo:
        'guardianFirstname': allBuyers_dict.get(i.buyerID, {}).get('firstname', None),
        'guardianLastname': allBuyers_dict.get(i.buyerID, {}).get('lastname', None),
        'guardianEmail': allBuyers_dict.get(i.buyerID, {}).get('email', None),
        'guardianPhoneNumber': allBuyers_dict.get(i.buyerID, {}).get('phoneNumber', None),
        'guardianAddress': allBuyers_dict.get(i.buyerID, {}).get('address', None),

      })

    # r = [
    #   {

    #     'acctEvent_id': i.event_id,
    #     'acctTransactionDateTimeUTC': i.transactionDateTime,
    #     'acctTransactionDateTimeLocal': i.transactionDateTime.astimezone( allCourses_dict.get(i.course_code).subdomain ),
    #     'acctSource': i.source,
    #     'acctLocalCurrencyChargedAmount': i.localCurrencyChargedAmount,
    #     'acctCurrency': i.currency,
    #     'acctLocalCurrencyServiceFee': lookupFees(i),

    #     # courseInfo
    #     'courseLocation': allCourses_dict.get(i.course_code, {}).get('formatLocation', None),
    #     'courseStartDate': allCourses_dict.get(i.course_code, {}).get('start_date', None),
    #     'courseEndDate': allCourses_dict.get(i.course_code, {}).get('end_date', None),
    #     'courseSubdomain': allCourses_dict.get(i.course_code, {}).get('subdomain', None),

    #     # parentInfo:
    #     'guardianFirstname': allBuyers_dict.get(i.buyerID, {}).get('firstname', None),
    #     'guardianLastname': allBuyers_dict.get(i.buyerID, {}).get('lastname', None),
    #     'guardianEmail': allBuyers_dict.get(i.buyerID, {}).get('email', None),
    #     'guardianPhoneNumber': allBuyers_dict.get(i.buyerID, {}).get('phoneNumber', None),
    #     'guardianAddress': allBuyers_dict.get(i.buyerID, {}).get('address', None),

    #   }


    # for i in allOrders]

    return r


  @classmethod
  def getAmortizedRevenueSchedule(cls, startDate=timezone.datetime.min , endDate=timezone.datetime.max):
    """
    show the amortized revenue from our books
    - assume each class date recieves a pro-rata revenue
    - say a course with 2 class dates (02/01/2017, 03/01/2017) is charged 100 HKD, 50 revenue will be booked for each class on those dates  
    """

    endDate = endDate.replace(hour = 23, minute=59, second = 59, microsecond=999999)

    allOrders = cls.objects.filter(
      livemode = True,
      transactionDateTime__gte = startDate, 
      transactionDateTime__lte = endDate
    )

    # list of course_codes from Ledger
    course_codes_list = [order.course_code for order in allOrders]

    allCourses = Course.objects.filter(course_code__in = course_codes_list).prefetch_related('courseclassdaterelationship_set')

    # inspect the class dates and the count and put them in a courseMemo for lookup / memo
    courseMemo = {}
    for c in allCourses:
      courseMemo[c.course_code] = [ d.startDateTime for d in c.courseclassdaterelationship_set.all() if d.ignore == False ]

    # actually process the ledger items now, split into currency
    r = []
    for o in allOrders:

      classDates = courseMemo.get(o.course_code, [])

      if len(classDates) == 0:
        r.append({
          'date': o.transactionDateTime,
          'currency': o.currency,
          'amt': o.localCurrencyChargedAmount,
          'course_code': o.course_code,
        })
        # go to the next order, just book revenue on transaction date
        continue

      # otherwise for every date of the course there we book a revenue
      for date in classDates:

        r.append({
          'date': date,
          'currency': o.currency,
          'amt': float(o.localCurrencyChargedAmount) / float(len(classDates)),
          'course_code': o.course_code,
        })

    return r

  class Meta:
    # event id is unique per strip acct
    unique_together = ('stripeAcct', 'event_id')
    





