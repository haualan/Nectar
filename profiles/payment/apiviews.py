from .utils import *
from rest_framework import viewsets, filters, generics, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from rest_framework.exceptions import APIException, ParseError, PermissionDenied
from .serializers import *

from course.models import Course
from .models import *

from .utils import *


import stripe

# Set your secret key: remember to change this to your live secret key in production
# See your keys here: https://dashboard.stripe.com/account/apikeys
# since FCA has multiple offices, we need to set this according to the webhooks
# setting HK here is just a default
stripe.api_key = settings.STRIPE_SECRET_MAP.get('hkd')


from threading import Thread
def postpone(function):
  def decorator(*args, **kwargs):
    t = Thread(target = function, args=args, kwargs=kwargs)
    t.daemon = True
    t.start()
  return decorator


class StripeWebhookView(views.APIView):
  """
  rec'd events from stripe, here is a dummy event: \n
  {
  "created": 1326853478,
  "livemode": false,
  "id": "evt_00000000000000",
  "type": "charge.succeeded",
  "object": "event",
  "request": null,
  "pending_webhooks": 1,
  "api_version": "2016-10-19",
  "data": {
    "object": {
      "id": "ch_00000000000000",
      "object": "charge",
      "amount": 6600,
      "amount_refunded": 0,
      "application": null,
      "application_fee": null,
      "balance_transaction": "txn_00000000000000",
      "captured": true,
      "created": 1485330119,
      "currency": "hkd",
      "customer": "cus_00000000000000",
      "description": "enroll student id: 328, course_code : CN17-AC-WP-0207-SW, name: Web Programming with JavaScript",
      "destination": null,
      "dispute": null,
      "failure_code": null,
      "failure_message": null,
      "fraud_details": {},
      "invoice": null,
      "livemode": false,
      "metadata": {
        "studentID": "328",
        "course_name": "Web Programming with JavaScript",
        "course_code": "CN17-AC-WP-0207-SW"
      },
      "order": null,
      "outcome": {
        "network_status": "approved_by_network",
        "reason": null,
        "risk_level": "normal",
        "seller_message": "Payment complete.",
        "type": "authorized"
      },
      "paid": true,
      "receipt_email": "alan+30@firstcodeacademy.com",
      "receipt_number": null,
      "refunded": false,
      "refunds": {
        "object": "list",
        "data": [],
        "has_more": false,
        "total_count": 0,
        "url": "/v1/charges/ch_19flPnH0YJapodUQ7tmEhpIz/refunds"
      },
      "review": null,
      "shipping": null,
      "source": {
        "id": "card_00000000000000",
        "object": "card",
        "address_city": null,
        "address_country": null,
        "address_line1": null,
        "address_line1_check": null,
        "address_line2": null,
        "address_state": null,
        "address_zip": null,
        "address_zip_check": null,
        "brand": "Visa",
        "country": "US",
        "customer": "cus_00000000000000",
        "cvc_check": "pass",
        "dynamic_last4": null,
        "exp_month": 1,
        "exp_year": 2023,
        "funding": "credit",
        "last4": "4242",
        "metadata": {},
        "name": "alan+30@firstcodeacademy.com",
        "tokenization_method": null
      },
      "source_transfer": null,
      "statement_descriptor": null,
      "status": "succeeded"
    }
  }
}
  """

  api_name = 'stripewebhook'
  http_method_names = ['post']
  permission_classes = (AllowAny, )

  validEventTypes = ('charge.succeeded', 'charge.refunded')
  
  def post(self, request, format=None, *args, **kwargs):
    print request.data

    dataWrapper = request.data

    # extract the currency and find the stripe key based on currency
    currency = 'hkd'
    try:
      currency = dataWrapper.get('data').get('object').get('currency').lower()
    except:
      pass

    stripe.api_key = settings.STRIPE_SECRET_MAP.get( currency )


    try:
      event = stripe.Event.retrieve(dataWrapper["id"])

    except stripe.InvalidRequestError, e:
      raise PermissionDenied(u'InvalidRequestError: {}'.format(e))

    # we only care about charge success and refunds, all other is noise at this time
    event_type = dataWrapper['type']

    if event_type not in self.validEventTypes:
      # do not bother
      return Response({})

    event_id = dataWrapper['id']
    if Ledger.objects.filter(event_id = event_id).exists():
      # if the transaction already exists, ignore, as recommeded by stripe
      return Response({})


    # save the raw request and id info to the model and let model handlers fill in the rest of the fields
    ledgerObj = Ledger.objects.create(
      event_type = event_type,
      event_id = event_id,
      rawData = request.data,
      stripeAcct = currency,
    )

    print 'event_type', event_type == 'charge.succeeded'
    if event_type == 'charge.succeeded':
      self.broadcastChargeSucceeded(ledgerObj)
      


    # self.processPayload(request)
    # respond with a 200 if things are okay
    return Response({})

  @postpone
  def broadcastChargeSucceeded(self, ledgerObj):
    """ 
    all the responses the server should have upon the confirmation of a charge
    - send confirmation email to buyer
    - send some signal to internal team
    - update enrollment on codeninja
    """

    send_order_confirm_email(ledgerObj)

    # internally send an email to respective offices
    # if the email is not found, send to hk internal team

    c = ledgerObj.getCourseOrNone()
    if c is None:
      # if it doesn't exist, it's not a real class
      return

    # ssm = settings.SUBDOMAINSPECIFICMAPPING

    # defaultEmailTo = ssm.get('hk').get('emailFrom')

    # subdomainDict = ssm.get(c.subdomain, ssm.get('hk'))
    # emailTo = subdomainDict.get('emailFrom', defaultEmailTo)

    # for testing, just email to alan@
    # emailTo = 'alan@firstcodeacademy.com'

    send_internal_sales_email(ledgerObj)


    # tell codeninja about enrollment
    c.updateCodeNinjaEnrollment()


     




  def processPayload(self, request):
    """
    given a payload from stripe, extract details and add contents back into ledger
    """
    dataWrapper = request.data
    obj = dataWrapper['data']['object']

    event_type = dataWrapper['type']
    event_id = dataWrapper['id']

    livemode = dataWrapper['livemode']
    transactionDateTime = timezone.make_aware(timezone.datetime.fromtimestamp(obj['created']))
    currency = obj['currency']

    # these fields are not reliable for accounting purposes
    # amount = obj['amount']
    # amount_refunded = obj['amount_refunded']
    
    stripeCustomerId = obj['customer']

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



    ledgerObj = Ledger.objects.create(
      event_type = event_type,
      event_id = event_id,
      rawData = request.data,
      livemode = livemode,
      transactionDateTime = transactionDateTime,
      currency = currency,
      # amount = amount,
      # amount_refunded = amount_refunded,
      buyerID = buyerID,
      studentID = studentID,
      course_code = course_code,
      stripeCustomerId = stripeCustomerId,
    )



    return ledgerObj


class PaymentChargeUserView(views.APIView):
  """
  charges user on stripe
  """

  api_name = 'paymentchargeuser'
  http_method_names = ['post']
  permission_classes = (IsAuthenticated, )
  serializer_class = PaymentChargeUserSerializer

  def post(self, request, format=None, *args, **kwargs):
    serializer = self.serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)

    guardianUser = request.user
    print 'PaymentChargeUserView.... recd', serializer.validated_data

    studentID = serializer.validated_data.get('studentID')
    token = serializer.validated_data.get('token')
    course_code = serializer.validated_data.get('course_code')
    price_code = serializer.validated_data.get('price_code')
    coupon_code = serializer.validated_data.get('coupon_code', None)
    refCode = serializer.validated_data.get('refCode', None)
    refCreditList = serializer.validated_data.get('refCreditList', None)

    



    # make sure studentUser exists
    studentUser = guardianUser.get_myActiveStudents.filter(id = studentID)

    if not studentUser.exists():
      raise ParseError('StudentID does not exist or not a student of current user')

    studentUser = studentUser.first()


    # make sure course_code exists
    course = Course.objects.filter(course_code = course_code)

    if not course.exists():
      raise ParseError('course_code does not exist')

    course = course.first()

    # price_obj reference is from database supplied by codeninja
    price_obj = next((item for item in course.prices if item['price_code'] == price_code), None)

    if price_obj is None:
      raise ParseError('price_code does not exist')

    # set inital discount amount
    final_discount_amount = 0.0

    # apply referral discounts here
    if refCode:
      refCodeValidityDict = ReferralCredit.useReferralCode(
        referToUser = guardianUser, 
        subdomain = course.subdomain, 
        refCode = refCode,
      )

      if refCodeValidityDict.get('isValid'):
        final_discount_amount += refCodeValidityDict.get('discount')


    # apply referral Credits here
    if refCreditList:
      final_discount_amount += ReferralCredit.useReferralCreditList.useReferralCreditList(
        creditedUser = guardianUser,
        listOfIDs = refCreditList,
      )

    # apply coupon and discounts here    
    if coupon_code:
      couponValidityDict = useCodeNinjaCoupon(addlDiscount = final_discount_amount, course_code = course.course_code, coupon_code = coupon_code, price_code = price_code)
      if couponValidityDict.get('isValid'):
        final_discount_amount += couponValidityDict.get('discount')



    # check if student is already registered to class. do not want to pay twice
    if studentUser.usercourserelationship_set.filter(course = course).exists():
      raise ParseError('Student already enrolled to course')



    # Create a Customer on stripe if needed :
    if guardianUser.email is None:
      raise ParseError('Guardian User account must have an email for payment purposes')


    # currency is needed to locate the correct stripe key
    currency = price_obj.get('currency', '')
    stripe.api_key = settings.STRIPE_SECRET_MAP.get(currency.lower(), None)

    if stripe.api_key is None:
      raise ParseError('Currency not found: {}, cannot locate stripe key'.format(currency))


    # if stripeCustomerId does exist, verify its existence first
    if guardianUser.stripeCustomerId:
      try:
        cu = stripe.Customer.retrieve(guardianUser.stripeCustomerId)
      except stripe.InvalidRequestError, e:
        print 'PaymentChargeUserView stripe cus test error', e

        # stripe ID probably bad, discard henceforth
        guardianUser.stripeCustomerId = None

    if guardianUser.stripeCustomerId is None:
      customer = stripe.Customer.create(
        email = guardianUser.email,
        metadata = {'uid': guardianUser.id },
        source = token,

      )

      # save info in hummingbird
      guardianUser.stripeCustomerId = customer.id
      guardianUser.save() 
      guardianUser.refresh_from_db()

    # 

    # when guardian is a reg. customer is stripe, now start charging


    # addl. data to be included in the order 
    metadata={
      "studentID": studentUser.id,
      "course_code": course_code,
      "course_name": course.name,
      "buyerID": guardianUser.id,

    }



    # Charge the user's card:
    # twd, sgd, hkd currencies
    # 1 is 1 cent

    amt = price_obj.get('amount', None)


    if amt is None or currency is None:
      raise ParseError('course: {} incorrect prices config: {}'.format(course_code, price_code))


    # set coupon or discounts now
    amt = float(amt)
    amt = amt - final_discount_amount

    mult = currencyMultiplier.get(currency.lower(), None)
    if mult is None:
      raise ParseError('currency multiplier not recognized {}'.format(currency.lower()))

    # convert amt to decimal and apply multiplier (because stripe must use integers)
    stripeAmt = None
    try:
      stripeAmt = int(round( float(amt)/ mult))
    except Exception as e:
      raise ParseError('stripe currency conversion error: {} / {}'.format(amt, mult))




    charge = stripe.Charge.create(
      amount=stripeAmt,
      currency=currency.lower(),
      description="enroll student id: {}, course_code : {}, name: {}".format(studentUser.id, course_code, course.name),
      # source=token,
      customer = guardianUser.stripeCustomerId,
      metadata = metadata,
    )


    # when charge is successful, add student to course
    studentUser.usercourserelationship_set.create(course = course)


    # send user an email, handled when recieve payment happends
    # send_order_confirm_email(order)
    


    return Response({'status': 'success'}, status=200)



class PaymentManualChargeView(views.APIView):
  """
  charges user manually
  """

  api_name = 'paymentmanualcharge'
  http_method_names = ['post']
  permission_classes = (IsAuthenticated, )
  serializer_class = PaymentManualChargeSerializer

  def post(self, request, format=None, *args, **kwargs):
    serializer = self.serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)

    

    openTrans = Ledger.createManualCharge(**serializer.validated_data)

    # TBD: subscribe user to course
    # email user a receipt.


    return Response({'status': 'success', 'event_id': openTrans.event_id})


class PaymentManualRefundView(views.APIView):
  """
  charges user manually
  """

  api_name = 'paymentmanualrefund'
  http_method_names = ['post']
  permission_classes = (IsAuthenticated, )
  serializer_class = PaymentManualRefundSerializer

  def post(self, request, format=None, *args, **kwargs):
    serializer = self.serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)

    closingTrans = Ledger.createManualRefund(**serializer.validated_data)

    return Response({'status': 'success', 'event_id': closingTrans.event_id})



class LedgerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows ledger to be viewed only. 
    \n pass in a query param: buyerID, with a user's id to get accounting details for that customer
    \n - this is available generally for internal / office use only
    \n - if not authorized, may return only the logged in user's items

    """
    api_name = 'ledger'

    queryset = Ledger.objects.all()
    serializer_class = LedgerSerializer
    http_method_names = ['get']
    permission_classes = (IsAuthenticated,)

    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('buyerID',)

    def get_queryset(self): 

      u = self.request.user
      if u.role not in ('I', 'O', 'C'):  
        return self.queryset.filter(buyerID = u.id)

      if 'buyerID' not in self.request.query_params:
        raise ParseError('buyerID must be supplied as a query param for internal usage to prevent oversized queries')

      return self.queryset



class ReferralCreditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows available referral credits to be seen for the current logged in user
    """
    api_name = 'referralcredit'

    queryset = ReferralCredit.objects.all()
    serializer_class = ReferralCreditSerializer
    http_method_names = ['get']
    permission_classes = (IsAuthenticated,)

    def get_queryset(self): 

      u = self.request.user

      return self.queryset.filter(creditedUser = u, isUsed = False)




class CouponValidationView(views.APIView):
  """
  /n given a payload of 
  /n { 'coupon_code': 'SOMECOUPON', 'course_code': '123' }
  /n validate with code ninja to see if coupon is actually valid.

  Front end should update with price
  """
  api_name = 'couponvalidation'
  http_method_names = ['post']

  # it has to be public otherwise anonymous buyer cannot verify
  permission_classes = (AllowAny, )
  serializer_class = CouponValidationSerializer

  def post(self, request, format=None, *args, **kwargs):
    serializer = self.serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)

    coupon_code = serializer.validated_data.get('coupon_code')
    course_code = serializer.validated_data.get('course_code')
    price_code = serializer.validated_data.get('price_code')
    addlDiscount = serializer.validated_data.get('addlDiscount', 0)

    resultDict = validateCodeNinjaCoupon(addlDiscount = addlDiscount, coupon_code = coupon_code , course_code = course_code, price_code = price_code)
    return Response(resultDict)


class ReferralValidationView(views.APIView):
  """
  /n given a payload of 
  /n { 'refCode': '<some code>', 'subdomain': 'hk' }
  /n validate with code ninja to see if coupon is actually valid.

  Front end should update with price
  """
  api_name = 'referralvalidation'
  http_method_names = ['post']

  # only logged in users can attempt to validate referral code
  permission_classes = (IsAuthenticated, )
  serializer_class = ReferralValidationSerializer

  def post(self, request, format=None, *args, **kwargs):
    serializer = self.serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)

    refCode = serializer.validated_data.get('refCode')
    subdomain = serializer.validated_data.get('subdomain')

    # the user calling this endpoint is being referred
    referToUser = request.user


    resultDict = ReferralCredit.verifyReferralCode(
      referToUser = referToUser,
      refCode = refCode,
      subdomain = subdomain,
    )

    return Response(resultDict)










