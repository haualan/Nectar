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

        
        return self.queryset.filter(id=self.request.user.id)

    # def get(self, request, format=None):
    #     return Response(self.queryset.filter(email=self.request.user))

# class UserListView(generics.ListAPIView):
#     queryset = User.objects.all()
#     serializer = UserSerializer
#     filter_backends = (filters.SearchFilter,)
#     search_fields = ('username', 'email')

    
class UserPublicView(views.APIView):
    """
    \n    POST a payload with uid and slug and return user's public info, option to return more if user has relationship with student, or if role is instructor

        {
        "uid":"13"
        "slug":"bla-bla"
        }

    """
    api_name = 'userpublic'

    # this endpoint should be public so anyone can ask for public profile
    permission_classes = (AllowAny, )
    http_method_names =['post']

    def post(self, request, format=None, *args, **kwargs):
        viewingUser = request.user

        uid = request.data.get('uid')
        slug = request.data.get('slug')

        if uid is None or slug is None:
            raise ParseError('uid or slug invalid')

        u = None
        isSlugValid = False
        try:
            u = User.objects.get(id = uid)
        except:
            raise ParseError('uid or slug invalid')

        if (u.slugName == slug):
            isSlugValid = True

        if not isSlugValid:
            raise ParseError('uid or slug invalid')

        # if viewingUser has relationship with u return comprehensive profile views
        # else return summary profile view

        comprehensiveProfile = MeSerializer(u, context={'request': request}).data
        return Response(comprehensiveProfile)




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
        email = request.data.get('email')

        if username is None and email is None:
            raise ParseError('username and email cannot be blank at least one must be filled')

        status = False

        if username:
            status = not User.objects.filter(username__iexact=username).exists()

        if email:
            status = not User.objects.filter(email=email).exclude(email__isnull = True).exists()

        return Response({
            'status': status,
        })

class StudentResetPWView(views.APIView):
    """
    Endpoint for user to reset password for his/her student
    {
    "uid": "2",
    "password1":"something",
    "password2":"something"
    }
    """

    api_name = 'studentresetpw'

    # this endpoint should be public so anyone can sign up / create user
    permission_classes = (IsAuthenticated,)
    http_method_names =['post']
    serializer_class = StudentResetPWSerializer


    def post(self, request, format=None, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        password1 = serializer.validated_data.get('password1')
        password2 = serializer.validated_data.get('password2')
        uid = serializer.validated_data.get('uid')

        if password1 != password2:
            raise ParseError('password1 does not match password2')

        if not request.user.isMyStudent(uid):
            raise ParseError('uid: {} not your student'.format(uid))

        targetUser = User.objects.get(id = uid)
        # actual reset pw
        targetUser.set_password(password1)
        targetUser.save()


        return Response({'status': 'success'})

class StudentDeactivateView(views.APIView):
    """
    Endpoint for user to reset password for his/her student
    {
    "uid": "2",
    "password1":"something",
    "password2":"something"
    }
    """

    api_name = 'studentdeactivate'

    # this endpoint should be public so anyone can sign up / create user
    permission_classes = (IsAuthenticated,)
    http_method_names =['post']
    serializer_class = StudentDeactivateSerializer


    def post(self, request, format=None, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data.get('uid')

        if not request.user.isMyStudent(uid):
            raise ParseError('uid: {} not your student'.format(uid))

        targetUser = User.objects.get(id = uid)
        # actual reset pw
        targetUser.is_active = False
        targetUser.save()


        return Response({'status': 'success'})


class UserCreateView(views.APIView):
    """
\n    1. POST a payload with username , password1, password2 to create a user 
\n token is returned upon successful creation
        {
        "username":"alan",
        "password1":"1q2w3e4r",
        "password2":"1q2w3e4r",
        "role": "S",
        "verifyToken": "???"
        }

    """

    api_name = 'usercreate'

    # this endpoint should be public so anyone can sign up / create user
    permission_classes = (AllowAny, )
    http_method_names =['post']
    serializer_class = UserCreateSerializer

    # consider adding a token payload in the body to bar access from unwanted websites

    def post(self, request, format=None, *args, **kwargs):
        # print 'isAnon?', request.user.is_anonymous()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # user = self.perform_create(serializer)

        # print serializer.validated_data
        # print request.META

        email = serializer.validated_data.get('email')
        username = serializer.validated_data.get('username')
        password1 = serializer.validated_data.get('password1')
        password2 = serializer.validated_data.get('password2')
        role = serializer.validated_data.get('role')
        verifyToken = serializer.validated_data.get('verifyToken')
        isMyStudent = serializer.validated_data.get('isMyStudent')
        gender = serializer.validated_data.get('gender', 'M')

        firstname = serializer.validated_data.get('firstname', "")
        lastname = serializer.validated_data.get('lastname', "")

        # confirm that frontend has a signature passed
        if verifyToken != settings.VERIFYTOKEN:
            raise PermissionDenied('Verification Token missing or invalid')

        # if username is None or password1 is None or password2 is None or email is None or role is None:
        #     raise ParseError('one or more required fields are missing')

        if password1 != password2:
            raise ParseError('password1 does not match password2')

        if username is None and email is None:
            raise ParseError('At least username or email must be filled')


        # avatar_url = User._meta.get_field('avatar_url').default
        # if gender == 'M':
        #     avatar_url = 'https://s3-ap-southeast-1.amazonaws.com/fcanectar/customMedia/defaultUserIconBoy.png'


        try:
            user = User.objects.create(username=username, email=email, role=role, gender=gender, firstname=firstname, lastname=lastname)
        except IntegrityError as e:
            raise ParseError('username is not unique or email incorrect: {}'.format(e))

        user.set_password(password1)
        user.save()

        token, _ = Token.objects.get_or_create(user=user)

        # print request.data

        # if isMyStudent is True and this user is logged in / not anonymous, then associate user with parent student relationship
        if isMyStudent == True and request.user.is_anonymous() == False:
            guardianUser = request.user
            studentUser = user
            guardianUser.createMyStudentRelation(studentUser)

        r = {'id': user.id, 'key': token.key}

        return Response(r, status=status.HTTP_201_CREATED)




class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows current authenticated user to be viewed or edited.
    GET for all users, pass in ?myself=1 to see only yourself
    PUT to amend the current user

    """
    api_name = 'userprofile'

    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    http_method_names = ['get', 'put', 'patch', 'head', 'options', 'trace']
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', 'email')


    def get_queryset(self):
        # print 'UserProfileViewSet query_params', self.request.query_params
        # print 'self.request.build_absolute_uri()', self.request.build_absolute_uri()
        myself = self.request.query_params.get('myself', None)
        if myself:
            return self.queryset.filter(id=self.request.user.id)
        else:
            return self.queryset.filter(
                Q(isSearchable=True) | Q(id=self.request.user.id) | Q(id=self.request.user.get_myActiveStudents)
            )

        # examples:
        # User.objects.filter(Q(isSearchable=True) | Q(id=u.id) | Q(id=u.get_myActiveStudents) )

    def perform_update(self, serializer):
        print "serializer.validated_data", serializer.validated_data 


        
        # if serializer.validated_data.get('email') == self.request.user.email:
        #     print 'same email', self.request.user.email
        origUser = self.get_object()


        if origUser != self.request.user and origUser not in self.request.user.get_myActiveStudents:
            raise PermissionDenied('you have no relationship with this user')

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


class SchoolUpdateOrCreateView(views.APIView):
    """
    defines the School object, POST only
    \n use post to update or create the newest School
    """
    api_name = 'schoolupdateorcreate'
    # queryset = School.objects.all()
    serializer_class = SchoolUpdateOrCreateSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names= ('post', 'options')

    def post(self, request, format=None, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, partial=True)

        

        serializer.is_valid(raise_exception=True)
        # validated_data= request.data
        validated_data= serializer.validated_data

        # school = serializer.validated_data.get('school')
        # print 'post validation', validated_data

        defaults = validated_data

        # since avatar_url cannot be none in model, do not allow none to be passed
        if 'avatar_url' in defaults and defaults['avatar_url'] is None:
            defaults.pop('avatar_url',None)


        sch, created = School.objects.update_or_create(
            place_id = validated_data.get('place_id', None),

            # if an extremely similar activity already exists, then don't copy
            defaults = defaults
        )

        # example:
        # place_id = '"ChIJfTpQvOMBBDQRSu4cWMrwV_U"'
        # sch, created = School.objects.update_or_create(
        #     place_id = place_id,
        #     defaults = {
        #         'avatar_url': avatar_url,
        #         'name': name,
        #         'lon': lon,
        #         'lat': lat,
        #         'formatted_address': formatted_address
        #     }
        # )

        savedSchool = SchoolSerializer(sch, context={'request': request})

        return Response(savedSchool.data)



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




# class UserSchoolRelationViewSet(viewsets.ModelViewSet):
#     """
#     defines the School objects that could be associated with a user under UserSchoolRelation
#     """
#     api_name = 'userschoolrelation'
#     queryset = UserSchoolRelation.objects.all()
#     serializer_class = UserSchoolRelationSerializer
#     permission_classes = (IsAuthenticated,)

#     def get_queryset(self):

#         return self.queryset.filter( user=self.request.user)




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
    search_fields = ('firstname', 'lastname', 'email', 'id')

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

# from rest_auth.models import TokenModel
from profiles.adapter import manual_send_confirmation_mail
class SendConfirmationView(views.APIView):
    """
\n    1. POST a payload with name and email to invite a user 
    """

    api_name = 'sendconfirmation'

    # this endpoint should be public so anyone can sign up
    permission_classes = (IsAuthenticated, )
    http_method_names =['post']

    def post(self, request, format=None, *args, **kwargs):
        user = request.user

        print 'sendconfirmation...', user.email

        manual_send_confirmation_mail(user)

        # complete_signup(self.request._request, user,
        #     True,
        #     None)

        r = {'id': user.id, 'email': user.email}

        return Response(r)





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



from profiles.payment.apiviews import *
from profiles.internal.apiviews import *

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


