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

subdomainSpecificMapping = settings.SUBDOMAINSPECIFICMAPPING

def send_internal_sales_email(order, injectEmail=None):
  """
  when an order is made, send an internal email to team
  """
  return send_order_confirm_email(order = order, isInternal = True)



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

    email = subdomainSpecificMapping.get(subdomain).get('emailFrom')
    subdomain = course.subdomain

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

