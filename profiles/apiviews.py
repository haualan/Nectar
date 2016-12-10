from .models import *
from .permissions import *

from django.db.models import Q

from rest_framework import viewsets, filters, generics, views
from profiles.serializers import *
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


# from activities.statistics.jackdaniels import get_10K_duration_from_FTP



# rest framework Endpoints

# from .segment import *
class MeView(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that shows all the links open to the current user for a navigation bar, this is read-Only
    
    \n notification_id_topic_id: the first item is the notfication_id, the second is the topic_id, when showing stream to user, if topic_id matches this list...
    \n then for each notification_id, send a PUT to the /topicnotification/'notification_id'/ endpoint to signify a read action
    """
    api_name = 'me'

    queryset = User.objects.all()
    serializer_class = MeSerializer
    http_method_names = ['get']
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        # every time this query is called, it kicks off an insert to user profile that the user has logged in.

        # print self.request._request.session
        # print self.request.session.items()
        # for i in self.request.session.keys():
        #     print i 


        # self.request.user.record_login()
        # getSegment(self.request, 'identify')

        
        return self.queryset.filter(email=self.request.user)

    # def get(self, request, format=None):
    #     return Response(self.queryset.filter(email=self.request.user))

# class UserListView(generics.ListAPIView):
#     queryset = User.objects.all()
#     serializer = UserSerializer
#     filter_backends = (filters.SearchFilter,)
#     search_fields = ('username', 'email')

class UserValidateView(views.APIView):
    """
\n    POST a payload with username and returns status: true if available for use 

        {
        "username":"alan"
        }

    """

    api_name = 'uservalidate'

    # this endpoint should be public so anyone can sign up / create user
    permission_classes = (AllowAny, )
    http_method_names =['post']

    def post(self, request, format=None, *args, **kwargs):
        username = request.data.get('username')

        if username is None:
            raise ParseError('username cannot be blank')

        status = not User.objects.filter(username__iexact=username).exists()

        return Response({
            'status': status,
        })



class UserCreateView(views.APIView):
    """
\n    1. POST a payload with username , password1, password2 to create a user 
\n token is returned upon successful creation
        {
        "username":"alan",
        "password1":"1q2w3e4r",
        "password2":"1q2w3e4r"
        }

    """

    api_name = 'usercreate'

    # this endpoint should be public so anyone can sign up / create user
    permission_classes = (AllowAny, )
    http_method_names =['post']

    def post(self, request, format=None, *args, **kwargs):
        # serializer = self.serializer_class(data=request.data)
        # serializer.is_valid(raise_exception=True)
        # user = self.perform_create(serializer)

        username = request.data.get('username')
        password1 = request.data.get('password1')
        password2 = request.data.get('password2')

        if username is None or password1 is None or password2 is None:
            raise ParseError('one or more required fields are missing')

        if password1 != password2:
            raise ParseError('password1 does not match password2')

        try:
            user = User.objects.create(username=username,)
        except IntegrityError as e:
            raise ParseError('username is not unique: {}'.format(e))

        user.set_password(password1)

        token, _ = Token.objects.get_or_create(user=user)

        # print request.data

        r = {'id': user.id, 'key': token.key}

        return Response(r, status=status.HTTP_201_CREATED)




class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows current authenticated user to be viewed or edited.
    GET for all users, pass in ?myself=1 to see only yourself
    PUT to amend the current user
    DELETE to delete the current user

    """
    api_name = 'userprofile'

    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,IsOwnerOrReadOnly,)
    # http_method_names = ['get','put', 'patch', 'delete']
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', 'email')


    def get_queryset(self):
        # print 'UserProfileViewSet query_params', self.request.query_params
        # print 'self.request.build_absolute_uri()', self.request.build_absolute_uri()
        myself = self.request.query_params.get('myself', None)
        if myself:
            return self.queryset.filter(email=self.request.user)
        else:
            return self.queryset.filter(
                Q(isSearchable=True) | Q(email=self.request.user))

    def perform_update(self, serializer):
        # print "serializer.initial_data", serializer.initial_data 
        # if serializer.validated_data.get('email') == self.request.user.email:
        #     print 'same email', self.request.user.email
        origUser = self.get_object()

        u = serializer.save()



class UserFileViewSet(viewsets.ModelViewSet):
    """
    defines the relationship between students and guardians, each field is a user
    """
    api_name = 'userfile'
    queryset = UserFile.objects.all()
    serializer_class = UserFileSerializer
    permission_classes = (IsAuthenticated,)




class GuardianStudentRelationViewSet(viewsets.ModelViewSet):
    """
    defines the relationship between students and guardians, each field is a user
    """
    api_name = 'guardianstudentrelation'
    queryset = GuardianStudentRelation.objects.all()
    serializer_class = GuardianStudentRelationSerializer
    permission_classes = (IsAuthenticated,)



class SchoolViewSet(viewsets.ModelViewSet):
    """
    defines the School objects that could be associated with a user under UserSchoolRelation
    """
    api_name = 'school'
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = (IsAuthenticated,)




# class UserSchoolRelationUpdateOrCreate(views.APIView):
#     """
#     defines the School objects that could be associated with a user under UserSchoolRelation
#     \n use post to update or create the newest relationship
#     """
#     api_name = 'userschoolrelationupdateorcreate'
#     queryset = UserSchoolRelation.objects.all()
#     serializer_class = UserSchoolRelationSerializer
#     permission_classes = (IsAuthenticated,)
#     http_method_names= ('post', 'options')

#     def post(self, request, format=None, *args, **kwargs):
#         serializer = self.serializer_class(data=request.data, context={'request': request})

        

#         serializer.is_valid(raise_exception=False)


#         school = serializer.validated_data.get('school')
#         print 'post validation', school


#         usr, created = UserSchoolRelation.objects.update_or_create(
#             # followAnnouncement = announcement,

#             # if an extremely similar activity already exists, then don't copy
#             school = school,

#             user = self.request.user,
#             # defaults = defaults
#         )

#         return Response(r, status=status.HTTP_201_CREATED)




class UserSchoolRelationViewSet(viewsets.ModelViewSet):
    """
    defines the School objects that could be associated with a user under UserSchoolRelation
    """
    api_name = 'userschoolrelation'
    queryset = UserSchoolRelation.objects.all()
    serializer_class = UserSchoolRelationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):

        return self.queryset.filter( user=self.request.user)




class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed only. Less data available than UserProfile, but more concise
    GET available only
    \n pass in a query param: traineeUser_id, with a user's id to get a list of users that can be mentioned for this user
    \n - this will include all the experts of the user
    \n - this will include all the group coaches of the subscribed groups of the user

    """
    api_name = 'user'

    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get']
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', 'email')

    def get_queryset(self):

        return self.queryset.filter( Q(isSearchable=True) | Q(email=self.request.user))



# class CreateUserViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint that allows users to be created, which does not require user to be logged in, but only allows POST
#     POST available only
#     """
#     api_name = view_names_base['UserSerializer']

#     queryset = User.objects.all()
#     serializer_class = CreateUserSerializer
#     http_method_names = ['post']
#     # should not require permissions, open to public? or maybe require some request header to identify request coming from app?


# from rest_framework.generics import CreateAPIView
from .registration import InviteSerializer
# from rest_auth.app_settings import (TokenSerializer,
#                                     create_token)

from rest_framework.authtoken.models import Token
from allauth.account.utils import complete_signup

# from rest_auth.models import TokenModel
class InviteView(views.APIView):
    """
\n    1. POST a payload with name and email to invite a user 
    """

    api_name = 'invite'
    serializer_class = InviteSerializer

    # this endpoint should be public so anyone can sign up
    permission_classes = (AllowAny, )
    http_method_names =['post']

    # http_method_names = ['options','post', 'head','get']


    # allowed_methods = ('POST', 'OPTIONS', 'HEAD')
    # token_model = TokenModel

    # def get_response_data(self, user):
    #     if allauth_settings.EMAIL_VERIFICATION == \
    #             allauth_settings.EmailVerificationMethod.MANDATORY:
    #         return {}

    #     return TokenSerializer(user.auth_token).data

    def post(self, request, format=None, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)

        r = {'id': user.id, 'email': user.email}

        return Response(r, status=status.HTTP_201_CREATED)


    def perform_create(self, serializer):
        user = serializer.save(self.request)
        # create_token(self.token_model, user, serializer)
        token, _ = Token.objects.get_or_create(user=user)
        # complete_signup(self.request._request, user,
        #                 allauth_settings.EMAIL_VERIFICATION,
        #                 None)

        # switch allauth_settings.EMAIL_VERIFICATION to True by default

        print 'invite user', token, _
        complete_signup(self.request._request, user,
                        True,
                        None)


        return user

from social.actions import do_disconnect
class DisconnectSocialView(views.APIView):
    """
    POST to disconnect a social backend, association_id is an optional integer passed to selectively delete social associations of the same backend (i.e. if our account is associated with 2 facebook accounts...)
    \n sample payload:
    {
        'backend': 'strava',
    }

    """

    api_name = 'disconnectsocial'
    serializer_class = DisconnectSocialSerializer
    permission_classes = (IsAuthenticated, )
    http_method_names = ['post']


    def post(self, request, format=None, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        association_id = serializer.validated_data.get('association_id', None)
        backend = serializer.validated_data.get('backend')

        

        # check if backend makes sense
        if not request.user.social_auth.filter(provider = backend):
            raise ParseError("not a valid backend for this user")

        backend = request.user.social_auth.filter(provider = backend).first().get_backend_instance()

        if association_id:
            backend = request.user.social_auth.get(id = association_id ).get_backend_instance()

        do_disconnect(backend, 
            request.user, 
            association_id,
            redirect_name=None)

        return Response({'message':'disconnect successful', 'backend': serializer.validated_data.get('backend')})


class EmailConfirmView(views.APIView):
    """
    POST to confirm the email for registration / invite link

    """

    api_name = 'emailconfirm'
    # serializer_class = DisconnectSocialSerializer
    permission_classes = (AllowAny, )
    http_method_names = ['post']

    def post(self, request, format=None, *args, **kwargs):
        # serializer = self.serializer_class(data=request.data)
        # serializer.is_valid(raise_exception=True)

        # response = {}
        # response['userkey'] = key

        # response['resetPassword'] = resetPassword

        key = request.data.get('key')

        confirmed = EmailConfirmation.objects.filter(
            key = key, 
            sent__gte = timezone.now() - timezone.timedelta(days = settings.ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS) 
        )
        
        if not confirmed:
          raise PermissionDenied('invalid or expired key')

        confirmed = confirmed.first()

        user = User.objects.filter(email = confirmed.email_address.user)

        if not user:
          raise PermissionDenied('User does not exists')
        user = user.first()
        

        token = Token.objects.filter(user = user)
        if not token:
          token, _ = Token.objects.get_or_create(user=user)
        else:
          token = token.first()

        # response['token'] = token.key

        # verify email
        confirmed.email_address.verified = True
        confirmed.email_address.set_as_primary(conditional=True)
        confirmed.email_address.save()



        return Response({ 'token': token.key })



# from profiles.payment.apiviews import *

# collect all ModelViewSet class members of this module, must be at end of file
clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
clsmembers = filter(lambda x: issubclass(x[1], viewsets.ModelViewSet )  \
                    or issubclass(x[1], viewsets.ReadOnlyModelViewSet ) \
                    or issubclass(x[1], views.APIView ) \
                    # or issubclass(x[1], CreateAPIView ) \
                    , clsmembers)


# # collect all ModelViewSet class members of this module, must be at end of file
# clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
# clsmembers = filter(lambda x: issubclass(x[1], viewsets.ModelViewSet )  \
#                     or issubclass(x[1], viewsets.ReadOnlyModelViewSet ) \
#                     or issubclass(x[1], views.APIView ), clsmembers)


