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

from dateutil.parser import parse as dateTimeParse


import requests
# from allauth.account.models import EmailAddress, EmailConfirmation

subdomainSpecificMapping = settings.SUBDOMAINSPECIFICMAPPING

def send_internal_sales_email(order, injectEmail=None):
  """
  when an order is made, send an internal email to team
  """
  return send_order_confirm_email(order = order, isInternal = True, injectEmail=injectEmail)



def send_order_confirm_email(order, isInternal = False, injectEmail=None):
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

  if isInternal:
    html = renderOrderConfirmTemplate(payload ,isHtml = True, isInternal=True)
    text = renderOrderConfirmTemplate(payload, isHtml = False, isInternal=True)

    subdomain = course.subdomain
    email = subdomainSpecificMapping.get(subdomain).get('emailFrom')
    

    # hk serves as a fallback
    if len(subdomain) == 0:
      subdomain = 'hk'
    email = subdomainSpecificMapping.get(subdomain).get('emailFrom')

    # email can be overriden upstream
    if injectEmail:
      email = injectEmail

    formatPriceStr = order.formatPriceStr()

    subject = '[{} - {}] {} Signup {} by {}'.format('TEST', subdomain, formatPriceStr, order.course_code, email)
    if order.livemode:
      subject = '[{} - {}] {} Signup {} by {}'.format('LIVE', subdomain, formatPriceStr, order.course_code, email)

    
    return send_email(email, subject, text, html, subdomain )


  html = renderOrderConfirmTemplate(payload ,isHtml = True)

  text = renderOrderConfirmTemplate(payload, isHtml = False)

  subject = 'First Code Academy Registration Confirmation'

  subdomain = course.subdomain

  return send_email(email, subject, text, html, subdomain )




  # print r.status_code, context['email'],  context['recipient_name'], context['subject'],  r.text








def send_email(email, subject, text, html, subdomain = 'hk' ):
  """
  base function for sending email
  """

  # hk serves as a fallback
  if len(subdomain) == 0:
    subdomain = 'hk'

  r = requests.post(
    settings.MAILGUN_API_URL,
    auth=("api", settings.MAILGUN_KEY),
    data={"from": subdomainSpecificMapping.get(subdomain).get('emailFrom'),
          "h:Reply-To": subdomainSpecificMapping.get(subdomain).get('emailFrom'),
          "to": email,
          "subject": subject,
          "text": text,
          "html": html,
          
          "bcc" : 'michelle@firstcodeacademy.com, alan@firstcodeacademy.com',

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
  subdomain = 'hk'

  return send_email(email, subject, text, html, subdomain )


def renderOrderConfirmTemplate(p={}, isHtml = False, isInternal = False):

  """
  to be generated for a text based email, c is the context passed to render the string
  p the payload requires, <guardian User>, <Student User>, <course>, <order>
  """
  guardian = p.get('guardian')
  guardianFirstname = guardian.firstname.title()

  if not guardianFirstname:
    guardianFirstname = 'Guardian / Parent'

  student = p.get('student')
  studentFirstname = student.firstname.title()

  if not studentFirstname:
    studentFirstname = student.displayName


  course = p.get('course')

  
  firstTime = course.firstTime()
  lastTime = course.lastTime()
  courseName = course.name
  courseEventType = course.event_type
  formatLocation = course.formatLocation()

  subdomain = course.subdomain

  firstDate = course.firstDate()
  lastDate = course.lastDate()

  dateStr = firstDate
  if courseEventType in ['term', 'camp']:
    dateStr = '{} - {}'.format(firstDate, lastDate)


  internalName = subdomainSpecificMapping.get(subdomain).get('internalName')
  fullClassCalendarUrl = subdomainSpecificMapping.get(subdomain).get('fullClassCalendarUrl')
  officePhone = subdomainSpecificMapping.get(subdomain).get('officePhone')
  officeLocation = subdomainSpecificMapping.get(subdomain).get('officeLocation')
  emailFrom = subdomainSpecificMapping.get(subdomain).get('emailFrom')



  order = p.get('order')
  formatPriceStr = order.formatPriceStr()
  orderCode = order.event_id


  
  localizedTransactionDateTime = order.formatLocalizedTransactionDateTime()

  context = {
    'guardianFirstname': guardianFirstname,
    'studentFirstname': studentFirstname,
    # 'firstDate': firstDate,
    'dateStr': dateStr,

    'firstTime': firstTime,
    'lastTime': lastTime,
    'courseName': courseName,
    'formatLocation': formatLocation,
    'formatPriceStr': formatPriceStr,
    'localizedTransactionDateTime': localizedTransactionDateTime,
    'courseEventType': courseEventType,

    'fullClassCalendarUrl':fullClassCalendarUrl,
    'internalName': internalName,
    'officePhone': officePhone,
    'officeLocation': officeLocation,

    'emailFrom': emailFrom,

    'year': timezone.now().year,

    'orderCode': orderCode,

    'courseObj': course,
    'guardianObj': guardian,
    'studentObj': student,
    'orderObj': order,


  }


  print 'context'
  print context

  if isInternal == True:
    if isHtml == False:
      return render_to_string("account/email/internal_receipt.txt", context).strip()
    return render_to_string("account/email/internal_receipt.html", context).strip()

  if isHtml == False:
    return render_to_string("account/email/receipt.txt", context).strip()

  return render_to_string("account/email/receipt.html", context).strip()


def updateCodeNinjaEnrollment(order):
  """
  based on the course code attached to the order, send signal to codeninja on newest enrollment number
  usage example:
  - PATCH http://hk.firstcodeacademy.com/api/events/offerings/AT-SCRATCH-TRIAL-20170304-SW
  - payload = { "enrollment_count": 2 }
  """
  c = order.getCourseOrNone()


  if c is None:
    # course does not exist, abort
    return

  url = 'https://{}.firstcodeacademy.com/api/events/offerings/{}'.format(c.subdomain, c.course_code)

  enrollment_count = c.getEnrollment().count()

  jsonBody = { "enrollment_count": enrollment_count }

  r = requests.patch(
    url,
    headers={'Authorization': settings.CNKEY, 'Content-type': 'application/json', 'Accept': 'text/plain'},
    json=jsonBody
  )

  print 'updateCodeNinjaEnrollment',  r.status_code, r.url, jsonBody, {'Authorization': settings.CNKEY}

  if int(r.status_code) != 200:
    print r.text


  return r


# for easy pasting to shell_plus
# c = order.getCourseOrNone()
# url = 'https://{}.firstcodeacademy.com/api/events/offerings/{}'.format(c.subdomain, c.course_code)
# enrollment_count = c.getEnrollment().count()
# jsonBody = { "enrollment_count": enrollment_count }
# r = requests.patch(
#   url,
#   headers={'Authorization': settings.CNKEY, 'Content-type': 'application/json', 'Accept': 'text/plain'}, verify=False,
#   json=jsonBody
# )
# print 'updateCodeNinjaEnrollment',  r.status_code, r.url, jsonBody, {'Authorization': settings.CNKEY}
# if int(r.status_code) != 200:
#   print r.text


def useCodeNinjaCoupon(coupon_code, course_code, price_code):
  return validateCodeNinjaCoupon(coupon_code, course_code, useCoupon=True)


def validateCodeNinjaCoupon(coupon_code, course_code, price_code, useCoupon=False):
  """
  given coupon_code, send a get request to https://hk.firstcodeacademy.com/api/coupons
  and see if the coupon is valid for the course_code in question.
  - return True if valid, else False
  """

  if not coupon_code:
    p = {
      'reason': 'invalid coupon, coupon cannot be empty',
      'isValid': False,
      'discount_amount': 0.0,
    }
    return p

  if not course_code:
    p = {
      'reason': 'invalid coupon, course_code cannot be empty',
      'isValid': False,
      'discount_amount': 0.0,
    }
    return p
  
  course = Course.objects.filter(course_code = course_code)
  if not course:
    p = {
      'reason': 'course_code is invalid',
      'isValid': False,
      'discount_amount': 0.0,
    }
    return p

  course = course.first()



  cnHeaders = {'Authorization': settings.CNKEY}
  r = requests.get(url = 'https://hk.firstcodeacademy.com/api/coupons', headers = cnHeaders)


#   expect r.json() like this:
#   [
#   {
#     "id": 1,
#     "coupon_code": "SUMMEREARLY17",
#     "discount_amount": "380.0",
#     "currency": "HKD",
#     "use_type": "Unlimited",
#     "start_date": "2017-03-01",
#     "start_time": "2000-01-01T00:00:00.000Z",
#     "end_date": "2017-06-01",
#     "end_time": "2000-01-01T00:00:00.000Z",
#     "applicable_type": "Camp",
#     "course_code": "",
#     "use_capacity": 0,
#     "use_count": 0
#   }, ...
# ]

  for i in r.json():
    if i.get('coupon_code') == coupon_code:

      discount_amount = float(i.get('discount_amount', 0.0))

      currency = i.get('currency')
      use_type = i.get('use_type')

      start_date = dateTimeParse(i.get('start_date'))
      start_time = dateTimeParse(i.get('start_time'))
      end_date = dateTimeParse(i.get('end_date'))
      end_time = dateTimeParse(i.get('end_time'))


      use_count = int(i.get('use_count'))
      use_capacity = int(i.get('use_capacity'))

      applicable_type = i.get('applicable_type', '').lower()

      coupon_specific_course_code = i.get('course_code')


      # @kevon:
      # Logic for coupon

      # if applicable_type is "All" -> it works for Term/Camp/Event
      # if applicable_type is "Camp" -> it works only for Camp
      # if applicable_type is "Term" -> it works only for Term
      # if applicable_type is "Event" -> it works only for Event
      if applicable_type != 'all':
        # check if restriction applies to course
        if applicable_type != course.event_type.lower():
          print 'invalid coupon, applicable_type: {} does not apply to course_code {} with event_type: {}'.format(applicable_type, course_code, course.event_type.lower())
          p = {
            'reason': 'invalid coupon',
            'isValid': False,
            'discount_amount': 0.0,
          }
          return p

      # if use_type is "Unlimited" -> it works no matter what
      # if use_type is "Limited"-> check for use_count and use_capacity, if we still have quota, approve; if no quota left, deny
      if use_type != 'Unlimited':
        # check quota
        if use_count >= use_capacity:
          p = {
            'reason': 'invalid coupon, promotion has ended. Try earlier next time.',
            'isValid': False,
            'discount_amount': 0.0,
          }
          return p

      # if currency code does not match, throw error


      # if course_code is provided -> this coupon only works for this course/event (term/camp/event), deny if coupon_code and course_code do not match
      if coupon_specific_course_code:
        if course_code != coupon_specific_course_code:
          p = {
            'reason': 'invalid coupon, coupon does not apply to this product.',
            'isValid': False,
            'discount_amount': 0.0,
          }
          return p


      # if Today is not between start_date + starttime and end_date + end_time, deny the coupon use.
      if use_type != 'Unlimited':
        start_dateTime = start_date
        start_dateTime.replace(
          hour = start_time.hour, 
          minute = start_time.minute, 
          second = start_time.second, 
          microsecond = start_time.microsecond
        )

        end_dateTime = end_date
        end_dateTime.replace(
          hour = end_time.hour, 
          minute = end_time.minute, 
          second = end_time.second, 
          microsecond = end_time.microsecond
        )

        now = timezone.now()

        if now <= start_dateTime or now >= end_dateTime:
          print 'invalid coupon {}, invalid date range'.format(coupon_code)
          p = {
            'reason': 'invalid coupon, promotion has ended. Try earlier next time.',
            'isValid': False,
            'discount_amount': 0.0,
          }
          return p


      # If coupon's active = false, deny the coupon use
      # @alan, only active coupons are shown in API, so no need to check

      
      
      # after the payment is processed, hit the PATCH coupon API to update the use_count
      if useCoupon:
        # if actually using coupon, send a patch back to update the coupon
        new_use_count = use_count + 1
        payload = {
          'use_count': new_use_count
        }
        r = requests.patch(url = 'https://hk.firstcodeacademy.com/api/coupons/{}'.format(coupon_code), headers= cnHeaders, json=payload )
        
        if r.status_code != 200:
          print 'https://hk.firstcodeacademy.com/api/coupons/{}'.format(coupon_code), reason
          print r.text
          p = {
            'reason': "use coupon failed",
            'isValid': False,
            'discount_amount': 0.0,
          }
          return p

        p = {
          'reason': 'valid coupon, used for purchase',
          'isValid': True,
          'discount_amount': discount_amount,
        }
        return p

      p = {
        'reason': 'valid coupon',
        'isValid': True,
        'discount_amount': discount_amount,
      }
      return p


  print 'coupon {} not found in api'.format(coupon_code)
  p = {
    'reason': 'invalid coupon',
    'isValid': False,
    'discount_amount': 0.0,
  }
  return p




