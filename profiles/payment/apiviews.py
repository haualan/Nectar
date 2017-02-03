from .utils import *
from rest_framework import viewsets, filters, generics, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from rest_framework.exceptions import APIException, ParseError, PermissionDenied
from .serializers import *

from course.models import Course
from .models import *


import stripe

# Set your secret key: remember to change this to your live secret key in production
# See your keys here: https://dashboard.stripe.com/account/apikeys
stripe.api_key = settings.STRIPE_SECRET


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
    )

    # self.processPayload(request)
    # respond with a 200 if things are okay
    return Response({})

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

  # @postpone
  # def runProcesses(self):
  #     print 'runProcesses batch '
      
  #     c = checkAllAccountStatus()
      

      
  #     r = recordOrganizationAuditTrail()
      

  def post(self, request, format=None, *args, **kwargs):
    serializer = self.serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)

    guardianUser = request.user
    print 'PaymentChargeUserView.... recd', serializer.validated_data

    studentID = serializer.validated_data.get('studentID')
    token = serializer.validated_data.get('token')
    course_code = serializer.validated_data.get('course_code')



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

    # check if student is already registered to class. do not want to pay twice
    if studentUser.usercourserelationship_set.filter(course = course).exists():
      raise ParseError('Student already enrolled to course')



    # Create a Customer on stripe if needed :
    if guardianUser.email is None:
      raise ParseError('Guardian User account must have an email for payment purposes')


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
    amt = 400

    charge = stripe.Charge.create(
      amount=400,
      currency="hkd",
      description="enroll student id: {}, course_code : {}, name: {}".format(studentUser.id, course_code, course.name),
      # source=token,
      customer = guardianUser.stripeCustomerId,
      metadata = metadata,
    )


    # when charge is successful, add student to course
    studentUser.usercourserelationship_set.create(course = course)


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

    return {'status': 'success', 'event_id': openTrans.event_id}


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

    return {'status': 'success', 'event_id': closingTrans.event_id}




