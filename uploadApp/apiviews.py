from .models import *

from django.db.models import Q

from rest_framework import viewsets, filters, generics, views
from .serializers import *
import sys, inspect, itertools
from rest_framework.exceptions import APIException, ParseError, PermissionDenied
from rest_framework import status, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from django.utils import timezone
from django.conf import settings



class ProjectViewSet(viewsets.ModelViewSet):
    """
    defines the relationship between students and guardians, each field is a user
    """
    api_name = 'project'
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('user',)

class ProjectScreenshotViewSet(viewsets.ModelViewSet):
    """
    defines the relationship between students and guardians, each field is a user
    """
    api_name = 'projectsreenshot'
    queryset = ProjectScreenshot.objects.all()
    serializer_class = ProjectScreenshotSerializer
    permission_classes = (IsAuthenticated,)
	filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('project',)


class ProjectPackageFileViewSet(viewsets.ModelViewSet):
    """
    defines the School objects that could be associated with a user under UserSchoolRelation
    """
    api_name = 'projectpackagefile'
    queryset = ProjectPackageFile.objects.all()
    serializer_class = ProjectPackageFileSerializer
    permission_classes = (IsAuthenticated,)
	filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('project',)


class ProjectIconFileViewSet(viewsets.ModelViewSet):
    """
    defines the School objects that could be associated with a user under UserSchoolRelation
    """
    api_name = 'projecticonfile'
    queryset = ProjectIconFile.objects.all()
    serializer_class = ProjectIconFileSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('project',)



class ProjectSourceFileViewSet(viewsets.ModelViewSet):
    """
    defines the School objects that could be associated with a user under UserSchoolRelation
    """
    api_name = 'projectsourcefile'
    queryset = ProjectSourceFile.objects.all()
    serializer_class = ProjectSourceFileSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('project',)

# collect all ModelViewSet class members of this module, must be at end of file
clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
clsmembers = filter(lambda x: issubclass(x[1], viewsets.ModelViewSet )  \
                    or issubclass(x[1], viewsets.ReadOnlyModelViewSet ) \
                    or issubclass(x[1], views.APIView ) \
                    # or issubclass(x[1], CreateAPIView ) \
                    , clsmembers)