from .models import *
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

class TrophyRecordActionViewSet(viewsets.ModelViewSet):
    """
    defines the relationship between Instructor user and courses
    """
    api_name = 'trophyrecordaction'
    queryset = TrophyRecordAction.objects.all()
    serializer_class = TrophyRecordActionSerializer
    permission_classes = (IsAuthenticated,)





    
clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
clsmembers = filter(lambda x: issubclass(x[1], viewsets.ModelViewSet )  \
                    or issubclass(x[1], viewsets.ReadOnlyModelViewSet ) \
                    or issubclass(x[1], views.APIView ) \
                    # or issubclass(x[1], CreateAPIView ) \
                    , clsmembers)