#!/usr/bin/env python
# -*- coding: utf-8 -*-

from profiles.models import *
from django.utils import timezone
from course.models import internalEmailExclusionRegex, Course
from django.db.models import FloatField, IntegerField
from django.db.models.functions import Cast
import StringIO, requests
from django.conf import settings
import csv


internalEmailRecipients = [
  'michelle@firstcodeacademy.com', 
  'kevon@firstcodeacademy.com',
  'alan@firstcodeacademy.com',
  'hello@firstcodeacademy.com',
  ]

def send_internal_email(subject, text, html, file, subdomain = 'hk' ):
  """
  base function for sending email
  """

  # hk serves as a fallback
  if len(subdomain) == 0:
    subdomain = 'hk'

  r = requests.post(
    settings.MAILGUN_API_URL,
    auth=("api", settings.MAILGUN_KEY),
    files=[("attachment", ("report.csv",file))],

    data={"from": settings.SUBDOMAINSPECIFICMAPPING.get(subdomain).get('emailFrom'),
          "h:Reply-To": settings.SUBDOMAINSPECIFICMAPPING.get(subdomain).get('emailFrom'),
          "to": ', '.join(internalEmailRecipients),
          "subject": subject,
          "text": text,
          "html": html,
          })

  return r.status_code

def guardiansPendingPurchaseEmail(request):
  """
  wrapper for guardiansPendingPurchase, sends email 

  """
  r = guardiansPendingPurchase(request)

  csvfile = StringIO.StringIO()
  csvwriter = csv.writer(csvfile)

  # define the columns, also serve as keys
  cols = [ 'hoursWithoutPurchase','guardianEmail', 'guardianPhone', 'guardianFirstName', 'guardianLastName', 'guardianAddress' ]

  # write header
  csvwriter.writerow(cols)

  for row in r:
    csvwriter.writerow([u'{}'.format(row.get(i)) for i in cols])


  file = csvfile.getvalue()

  text = """
    <p>
    \n This report contains all users who signed up as a guardian after landing on the payments page (thereby showing high interest), 
    \n but haven't made purchase after 24 hours.
    </p>
    <ul>
      <li> - If the same user has not made a purchase for up till 7 days, the user will be dropped from the report (user no longer interested)
      </li>
      <li> - users signed up for less than 24 hrs are excluded from the report (maybe user is still deciding)
      </li>
    </ul>
    """

  subject = 'New Leads from Hummingbird'

  send_internal_email(
    subject = subject,
    text = text,
    html = text,
    file  = file
  )



  pass

def guardiansPendingPurchase(request):
  """
  finds all users (that are guardians) who has registered but hasn't made a purchase in the system
  - the idea behind this is that a buyer landed on the page, looking to pay but might be deterred from making actual payment what gives...
  - so, users in this state can be collected and tracked, so FCA can act upon them

  """

  buyerUserIDs = Ledger.objects.all().distinct('buyerID').annotate(user_id = Cast('buyerID', IntegerField()))

  # users registered within this window but hasn't made a purchase
  detectionWindowHours = 24.0

  # only consider users joined within this window
  longWindowDays = 7 

  now = timezone.now()
  hktz = timezone.pytz.timezone('Asia/Hong_Kong')

  r = User.objects.filter(
    date_joined__gte = now - timezone.timedelta(days = longWindowDays),
    role = 'G',
  ).exclude( 
    id__in = buyerUserIDs
  ).exclude(
    email__regex  = internalEmailExclusionRegex,
  )

  course_codes = set([ u.clientDump.get('paymentInterest', {}).get('course_code') for u in r if u.clientDump.get('paymentInterest', None) is not None ])
  courses = Course.objects.filter(course_code__in = course_codes)

  course_codes_dict = {
    c.course_code : c
    for c in courses
  }

  results = [
    { 

      
      
      'created_at_HKT': u.date_joined.astimezone(hktz),
      'hoursWithoutPurchase': (now - u.date_joined).total_seconds() / 3600.0,

      # could be none if course_code is stale
      'course_code': u.clientDump.get('paymentInterest', {}).get('course_code', None),

      'guardianEmail': u.email,
      'guardianFirstName': u.firstname,
      'guardianLastName': u.lastname,
      'guardianPhone': u.phoneNumber,
      'guardianAddress': u.address,
      'studentProfilesLinked': ', '.join([ u'{}:{}'.format(s.student.id, s.student.displayName)  for s in u.guardianstudentrelation_set.all()])

    }
    for u in r if (((now - u.date_joined).total_seconds() / 3600.0) >= detectionWindowHours)
  ]

  # pad results with subdomain
  for r in results:
    course_code = r.get('course_code')
    if course_code and course_codes_dict.get(course_code, False):
      r['subdomain'] = course_codes_dict.get(course_code).subdomain
      continue
    r['subdomain'] = None


  # sort by hoursWithoutPurchase
  results.sort(key= lambda x: x['hoursWithoutPurchase'] )

  return results


