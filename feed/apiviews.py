from .serializers import *
from rest_framework import viewsets, filters, generics, views

import sys, inspect, itertools
from rest_framework.exceptions import APIException, ParseError, PermissionDenied
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from django.utils import timezone
from django.conf import settings

# define custom dashboard api view here





# coursemates and people from your school should have their activity reported on your feed.

class FeedView(views.APIView):
    """
    POST to disconnect a social backend, association_id is an optional integer passed to selectively delete social associations of the same backend (i.e. if our account is associated with 2 facebook accounts...)
    \n sample payload:
    {
        'backend': 'strava',
    }

    """

    api_name = 'feed'
    # serializer_class = DisconnectSocialSerializer
    permission_classes = (IsAuthenticated, )
    http_method_names = ['get']


    def get(self, request, format=None, *args, **kwargs):

        return Response({})

















    
clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
clsmembers = filter(lambda x: issubclass(x[1], viewsets.ModelViewSet )  \
                    or issubclass(x[1], viewsets.ReadOnlyModelViewSet ) \
                    or issubclass(x[1], views.APIView ) \
                    # or issubclass(x[1], CreateAPIView ) \
                    , clsmembers)
