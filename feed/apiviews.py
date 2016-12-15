from .serializers import *
from rest_framework import views, viewsets, generics, permissions, filters, mixins

import sys, inspect, itertools
from rest_framework.exceptions import APIException, ParseError, PermissionDenied
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from django.db.models import F, Q, CharField, Case, Value, When
from django.db.models.functions import Coalesce

from django.utils import timezone
from django.conf import settings


from course.models import *
from .serializers import FeedSerializer


# define custom dashboard api view here





# coursemates and people from your school should have their activity reported on your feed.
#  3 types of activity: 1. Upload project, 2. Complete challenge, 3. Earn a trophy

class FeedView(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    GET only view for a users's dashboard to see:
    - other user's achievements
    - other classes going on
    - promotions... etc



    """

    api_name = 'feed'
    serializer_class = FeedSerializer
    permission_classes = (IsAuthenticated, )
    http_method_names = ['get']

    def injectTrophies(self):
        tr = TrophyRecord.objects.filter(

        ).annotate(
            date = F('createdDate'),
            user_fname = F('user__firstname'),
            user_lname = F('user__lastname'),
            user_avatar = F('user__avatar_url'),
            trophy_avatar = F('trophy__avatar_url'),
            trophy_name = F('trophy__name'),
        ).prefetch_related('user', 'trophy')


        return [{
            'date': i.createdDate,
            'type' : 'TrophyRecord',
            'id' : i.id,
            'user_avatar': i.user_avatar,
            'user_name': "{} {}".format(i.user_fname, i.user_lname),
            'trophy_avatar': i.trophy_avatar,
            'trophy_name': i.trophy_name

        } for i in tr]

    def injectChallenges(self):
        u = self.request.user
        cr = ChallengeRecord.objects.filter(
            # leave empty to select all
        ).annotate(
            date = F('createdDate'),
            user_fname = F('user__firstname'),
            user_lname = F('user__lastname'),
            user_avatar = F('user__avatar_url'),


        ).prefetch_related('user')

        return [{
            'date': i.createdDate,
            'type' : 'ChallengeRecord',
            'id' : i.id,
            'user_avatar': i.user_avatar,
            'user_name':i.user.displayName,
            # 'user_name': "{} {}".format(i.user_fname, i.user_lname)

        } for i in cr]

    def injectUploads(self):
        u = self.request.user
        p = u.project_set.model.objects.filter(
            # leave empty to select all
        ).annotate(
            date = F('updated'),
            user_fname = F('user__firstname'),
            user_lname = F('user__lastname'),
            user_avatar = F('user__avatar_url'),


        ).prefetch_related('user')

        return [{
            'date': i.date,
            'type' : 'Project',
            'id' : i.id,
            'name': i.name,
            # 'url': i.url,
            'user_avatar': i.user_avatar,
            'user_name': i.user.displayName,

        } for i in p]

      



    def get_queryset(self):
        u = self.request.user
        r = []

        r.extend(self.injectChallenges())
        r.extend(self.injectUploads())
        r.extend(self.injectTrophies())

        r.sort(key = lambda y: y['date'], reverse= True)



        return [{'item': j}for j in r]















clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
clsmembers = filter(lambda x: issubclass(x[1], viewsets.ModelViewSet )  \
                    or issubclass(x[1], viewsets.ReadOnlyModelViewSet ) \
                    or issubclass(x[1], views.APIView) \
                    or issubclass(x[1], viewsets.GenericViewSet) \
                        , clsmembers)
