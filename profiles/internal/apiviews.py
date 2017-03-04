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


class InternalView(views.APIView):
    """
    API endpoint for internal usage
    
    \n notification_id_topic_id: the first item is the notfication_id, the second is the topic_id, when showing stream to user, if topic_id matches this list...
    \n then for each notification_id, send a PUT to the /topicnotification/'notification_id'/ endpoint to signify a read action
    """
    api_name = 'internal'

    # queryset = User.objects.all()
    # serializer_class = MeSerializer
    http_method_names = ['post']
    permission_classes = (IsAuthenticated,)

    http_method_names =['post']

    def post(self, request, format=None, *args, **kwargs):
        viewingUser = request.user

        op = request.data.get('op', None)

        if op not in ['guardiansPendingPurchase']:
        	raise ParseError('expectinh operation variable op')



        r = globals()[op](request):




        

    def get_queryset(self):
        # every time this query is called, it kicks off an insert to user profile that the user has logged in.

        # print self.request._request.session
        # print self.request.session.items()
        # for i in self.request.session.keys():
        #     print i 


        # self.request.user.record_login()
        # getSegment(self.request, 'identify')

        
        return self.queryset.filter(id=self.request.user.id)




