from profiles.models import *


from rest_framework import viewsets, filters, generics, views

import sys, inspect, itertools
from rest_framework.exceptions import APIException, ParseError, PermissionDenied
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from django.utils import timezone
from django.conf import settings
from allauth.account.models import EmailAddress, EmailConfirmation
from rest_framework.authtoken.models import Token
from django.db import IntegrityError

from .utils import *

def getAuthToken(request):
  """
  returns the auth_token of the user, or None if user not found
  """
  user_id = request.data.get('user_id', None)
  u = User.objects.filter(id = user_id)

  if not u:
    return { 'token': '' }

  u = u.first()

  t, created = Token.objects.get_or_create(user = u)

  return { 'token': t.key }


class InternalView(views.APIView):
  """
  \n API endpoint for internal usage, mostly for AWS to trigger things since it requires a token
  
  \n
  \n find users looking to purchase but haven't done so for a period of time
  \n      {
  \n      "verifyToken": <token>,
  \n          "op": "guardiansPendingPurchase"
  \n      }
  \n same as above but fires the email to internal users
  \n      {
  \n          "verifyToken": <token>,
  \n          "op": "guardiansPendingPurchaseEmail"
  \n      }


  """
  api_name = 'internal'

  # queryset = User.objects.all()
  # serializer_class = MeSerializer
  http_method_names = ['post']
  permission_classes = (AllowAny,)


  def post(self, request, format=None, *args, **kwargs):
      # viewingUser = request.user

    verifyToken = request.data.get('verifyToken')

    # confirm that frontend has a signature passed
    if verifyToken != settings.VERIFYTOKEN:
      raise PermissionDenied('Verification Token missing or invalid')


    op = request.data.get('op', None)

    if op not in ['guardiansPendingPurchase', 'guardiansPendingPurchaseEmail']:
      raise ParseError('expecting operation variable op')

    return Response(globals()[op](request))


from course.models import UserCourseRelationship
from profiles.models import GuardianStudentRelation

def getAllEnrollmentReport(request):
  return UserCourseRelationship.getAllEnrollmentReport()

def getRevenueSchedule(request):
  return Ledger.getRevenueSchedule()

def getAllGuardianStudentsReport(request):
  return GuardianStudentRelation.getAllGuardianStudentsReport()

class InternalReportView(views.APIView):
  """
  \n API endpoint for internal usage, mostly for hummingbird internal frontend to generate reports
  \n
  \n enrollment report for all students
  \n      {
  \n          "op": "getAllEnrollmentReport"
  \n      }
  \n revenue schedule for all time
  \n      {
  \n          "op": "getRevenueSchedule"
  \n      }
  \n get auth token by user id
  \n      {
  \n          "op": "getAuthToken",
  \n          "user_id": 2
  \n      }


  """
  api_name = 'internalreport'

  # queryset = User.objects.all()
  # serializer_class = MeSerializer
  http_method_names = ['post']
  permission_classes = (IsAuthenticated,)


  def post(self, request, format=None, *args, **kwargs):
      # viewingUser = request.user

    if request.user.role not in ['I', 'O', 'C']:
      raise PermissionDenied('User not an internal officer')

    op = request.data.get('op', None)

    if op not in [ 'searchByReferralCode','getAllEnrollmentReport', 'getRevenueSchedule', 'getAllGuardianStudentsReport', 'getAuthToken']:
      raise ParseError('expecting operation variable op')

    return Response(globals()[op](request))


class UtilsView(views.APIView):
  """
  \n API endpoint for extrernal usage, mostly for publicly visible settings like referral code discount amounts
  \n
  \n subdomain settings
  \n      {
  \n          "op": "getSubdomainMapping"
  \n      }
  \n students of a guardian 
  \n      {
  \n          "op": "getStudents",
  \n          "uid": 2
  \n      }


  """
  api_name = 'utils'

  # queryset = User.objects.all()
  # serializer_class = MeSerializer
  http_method_names = ['post']
  permission_classes = (AllowAny,)


  def post(self, request, format=None, *args, **kwargs):
      # viewingUser = request.user

    op = request.data.get('op', None)

    if op not in ['getSubdomainMapping', 'getStudents']:
      raise ParseError('expecting operation variable op')

    return Response(globals()[op](request))

