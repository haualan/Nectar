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

  subject = 'First Code Academy Registration Confirmation'

  subdomain = course.subdomain

  return send_email(email, subject, text, html, subdomain )




  # print r.status_code, context['email'],  context['recipient_name'], context['subject'],  r.text






subdomainSpecificMapping = {
  'hk': {
    'internalName': 'Natasha',
    'fullClassCalendarUrl': 'https://hk.firstcodeacademy.com/en/programs/calendar',
    'emailFrom': 'hello@firstcodeacademy.com',
    'officePhone': '+852 2772 2108', 
    'officeLocation': 'Unit 302-305, 3/F, Hollywood Centre, 233 Hollywood Road, Sheung Wan, Hong Kong'
  },
  'sg': {
    'internalName': 'Wee Ping',
    'fullClassCalendarUrl': 'https://sg.firstcodeacademy.com/en/programs/calendar',
    'emailFrom': 'hellosg@firstcodeacademy.com',
    'officePhone': '+65 6820 2633',
    'officeLocation': '#04-13, Stamford Court, 61 Stamford Road, Singapore 178892'
  },
  'tw': {
    'internalName': 'Chi',
    'fullClassCalendarUrl': 'https://tw.firstcodeacademy.com/en/programs/calendar',
    'emailFrom': 'hello.tw@firstcodeacademy.com',
    'officePhone': '+886 909 818 260',

    # tw has no fixed location yet
    'officeLocation': ''

  },

}


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


def renderOrderConfirmTemplate(p={}, isHtml = False):

  """
  to be generated for a text based email, c is the context passed to render the string
  p the payload requires, <guardian User>, <Student User>, <course>, <order>
  """
  guardianFirstname = p.get('guardian').firstname

  if not guardianFirstname:
    guardianFirstname = 'Guardian / Parent'

  studentFirstname = p.get('student').firstname

  if not studentFirstname:
    studentFirstname = p.get('student').displayName


  course = p.get('course')

  

  firstTime = course.firstTime()
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


  
  localizedTransactionDateTime = order.localizedTransactionDateTime()

  context = {
    'guardianFirstname': guardianFirstname,
    'studentFirstname': studentFirstname,
    # 'firstDate': firstDate,
    'dateStr': dateStr,

    'firstTime': firstTime,
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





  }


  print 'context'
  print context


  if isHtml == False:
    return render_to_string("account/email/receipt.txt", context).strip()

  return render_to_string("account/email/receipt.html", context).strip()

