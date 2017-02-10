# -*- coding: utf-8 -*-

# import braintree, datetime
# from django.conf import settings
# from django.utils import timezone
# from django.contrib.auth import get_user_model
# # from profiles.models import Group, GroupMemberRelation, TraineeExpertRelation, Payment, Organization, OrganizationAuditTrail, ORG_TRAINEE, ORG_EXPERT, ORG_GROUPMEMBER

# # print 'braintree',braintree

# braintree.Configuration.configure(braintree.Environment.Sandbox,
#                                   merchant_id=settings.BRAINTREE_MERCHANT_ID,
#                                   public_key=settings.BRAINTREE_PUB_KEY,
#                                   private_key=settings.BRAINTREE_PRIV_KEY)

from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string

from course.models import Course


import requests
# from allauth.account.models import EmailAddress, EmailConfirmation



def send_order_confirm_email(order):
  # i.e.: on payment for example, we send a receipt
  # order is assumed to be a ledger object

  buyerUser = order.getBuyerUser()
  if buyerUser is None:
    print 'User does not exist...', order.buyerID
    return False

  email = buyerUser.email
  if email is None:
    print 'User email does not exist...', buyerUser.id,  buyerUser.displayName
    return False

  studentUser = order.getStudentUser()
  if buyerUser is None:
    print 'User does not exist...', order.studentID
    return False

  course = Course.objects.filter(course_code = order.course_code)
  if not course:
    print 'course does not exist...', order.course_code,
    return False

  course = course.first()


  payload = {
    'guardian': buyerUser,
    'student': studentUser,
    'course': course,
    'order': order,
  }

  html=  renderOrderConfirmTemplate(payload ,isHtml = True)

  text = renderOrderConfirmTemplate(payload, isHtml = False)

  subject = 'First Code Academy Order Confirmation'

  return send_email(email, subject, text, html )




  # print r.status_code, context['email'],  context['recipient_name'], context['subject'],  r.text


def send_email(email, subject, text, html ):
  """
  base function for sending email
  """

  r = requests.post(
    settings.MAILGUN_API_URL,
    auth=("api", settings.MAILGUN_KEY),
    data={"from": settings.DEFAULT_FROM_EMAIL,
          "h:Reply-To": "hello@firstcodeacademy.com",
          "to": email,
          "subject": subject,
          "text": text,
          "html": html,
          })

  return r.status_code


def send_test_email():
  """
  base function for sending email
  """
  email = 'alan@firstcodeacademy.com'
  subject = 'test email from server'
  text = 'test text'
  html = '<p>test html in email</p>'

  return send_email(email, subject, text, html )



def renderOrderConfirmTemplate(p={}, isHtml = False):

  """
  to be generated for a text based email, c is the context passed to render the string
  p the payload requires, <guardian User>, <Student User>, <course>, <order>
  """
  guardianFirstname = p.get('guardian').firstname

  if guardianFirstname is None:
    guardianFirstname = 'Guardian / Parent'

  studentFirstname = p.get('student').firstname


  firstDate = p.get('course').firstDate()
  firstTime = p.get('course').firstTime()
  courseName = p.get('course').name
  formatLocation = p.get('course').formatLocation()


  order = p.get('order')
  formatPriceStr = '{} {}'.format(order.localCurrencyChargedAmount, order.currency.upper())
  localizedTransactionDateTime = order.localizedTransactionDateTime

  context = {
    'guardianFirstname': guardianFirstname,
    'studentFirstname': studentFirstname,
    'firstDate': firstDate,
    'firstTime': firstTime,
    'courseName': courseName,
    'formatLocation': formatLocation,
    'formatPriceStr': formatPriceStr,
    'localizedTransactionDateTime': localizedTransactionDateTime,
  }


  print 'context'
  print context



  if isHtml == False:
    return u"""

    Order Confirmation

    Dear {[guardianFirstname]},

    I'm Natasha from First Code and I’d like to personally welcome you and {[studentFirstname]}. The term starts soon and we are very excited to see {[studentFirstname]} for the Fall term!

    We believe that coding can empower us to become creators and not just consumers of technology. It means a lot to us to have the opportunity to be part of this journey with your child.

    We have received your child’s information below:

    Day: {[firstDate]}
    Time: {[firstTime]}
    Course: {[courseName]}
    Location: {[formatLocation]}
    Full Class Calendar: https://hk.firstcodeacademy.com/en/programs/calendar



    Order Total: {[formatPriceStr]} <br>
    Order Date: {[localizedTransactionDateTime]} <br>


    Check our calendar for useful information about your schedule, what to bring to the class, what to do if you miss a class, how to find us etc.
    class calendar: https://hk.firstcodeacademy.com/en/programs/calendar

    Meanwhile, feel free to reach out to me via email or at 2772-2108 if you have any questions.


    We will see you and {[studentFirstname]} on 1st day of class on {[firstDate]}! 

    Kind regards,
    Natasha       
    Community Manager
    First Code Academy

    """.format(context)

  return render_to_string("account/email/receipt.html", context).strip()

