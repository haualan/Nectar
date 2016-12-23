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



from rest_framework.settings import api_settings
from rest_framework_csv import renderers as r



class MarketingViewSet(viewsets.ModelViewSet):
    """
    the marketing view
    """
    api_name = 'marketing'
    queryset = Marketing.objects.all()
    serializer_class = MarketingSerializer
    permission_classes = (AllowAny,)
    renderer_classes = [r.CSVRenderer, ] + api_settings.DEFAULT_RENDERER_CLASSES



class MarketingCustomView(views.APIView):
    """
\n    POST a payload with username and returns status: true if available for use 

        {
        "username":"alan"
        }

    """

    api_name = 'marketingcustom'

    # this endpoint should be public so anyone can sign up / create user
    permission_classes = (AllowAny, )
    http_method_names =['get']
    renderer_classes = [r.CSVRenderer, ] + api_settings.DEFAULT_RENDERER_CLASSES
    queryset = Marketing.objects.all()

    def get(self, request, *args, **kwargs):
    	return Response(list(self.queryset.values()))
        
        # return Response([
        #     {'status': 123},
        #     {'status': 323},
        # ])



    
clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
clsmembers = filter(lambda x: issubclass(x[1], viewsets.ModelViewSet )  \
                    or issubclass(x[1], viewsets.ReadOnlyModelViewSet ) \
                    or issubclass(x[1], views.APIView ) \
                    # or issubclass(x[1], CreateAPIView ) \
                    , clsmembers)