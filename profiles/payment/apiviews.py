from .utils import *
from rest_framework import viewsets, filters, generics, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from rest_framework.exceptions import APIException, ParseError, PermissionDenied
from .serializers import *

from course.models import Course


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



    # Create a Customer on stripe if needed :
    if guardianUser.email is None:
      raise ParseError('Guardian User account must have an email for payment purposes')

    if guardianUser.stripeCustomerId is None:
      customer = stripe.Customer.create(
        email = guardianUser.email,
        metadata = {'uid': guardianUser.id },
        source = token,

      )

      # save info in hummingbird
      guardianUser.save( stripeCustomerId = customer.id,  ) 
      guardianUser.refresh_from_db()

    # 

    # when guardian is a reg. customer is stripe, now start charging


    # addl. data to be included in the order 
    metadata={
      "studentID": studentUser.id,
      "course_code": course_code,
      "course_name": course.name,

    }

    # Charge the user's card:
    # twd, sgd, hkd currencies

    charge = stripe.Charge.create(
      amount=6600,
      currency="hkd",
      description="enroll student id: {}, course_code : {}, name: {}".format(studentUser.id, course_code, course.name),
      # source=token,
      customer = guardianUser.stripeCustomerId,
      metadata = metadata,
    )


    return Response({'status': 'success'}, status=200)

