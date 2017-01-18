
from profiles.models import *
# from activities.models import ZoneDefinition, CPnotification , PassiveActivityData
# from streamView.serializers import DMStreamMemberSerializer, TopicNotificationSerializer
from rest_framework import serializers

from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model, authenticate
from django.conf import settings
from django.db.models import Max, Min

from rest_framework import serializers, exceptions
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from allauth.account.models import EmailAddress, EmailConfirmation



from django.db.models import Avg, Count, F, Max, Min, Sum, Q, Prefetch

# from datetime import timedelta
import datetime, json

from rest_framework.fields import empty





class JSONSerializerField(serializers.Field):
    """ Serializer for JSONField -- required to make field writable"""
    def to_internal_value(self, data):
        # print 'JSONSerializerField data', type(data), data
        if type(data) != dict and type(data) != list:
            raise ParseError('expecting a dict or list instead of :{}'.format(data))
        return data
    def to_representation(self, value):
        # print 'JSONSerializerField value', type(value),value
        if type(value) != dict:
            return json.loads(value)

        # print 'to rep', value, self.default, value == {}
        if value == {} or value == []:
            # adhere to default representation if empty set or list is passed (because we don't know if user wants to save a list or dict) 
            # print 'returning self default'
            print 'self.default', self.default
            if self.default is not empty:
                return self.default
            return value

        return value

# from allauth.account.auth_backends import AuthenticationBackend
# backend = AuthenticationBackend()

class CustomLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'})

    def _validate_email(self, email, password):
        user = None

        if email and password:
            user = authenticate(email=email, password=password)
        else:
            msg = _('Must include "email" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def _validate_username(self, username, password):
        user = None

        if username and password:
            user = authenticate(username=username, password=password)
        else:
            msg = _('Must include "username" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def _validate_username_email(self, username, email, password):
        print '_validate_username_email'
        user = None

        if email and password:
            user = authenticate(email=email, password=password)
        elif username and password:
            user = authenticate(username=username, password=password)
        else:
            msg = _('Must include either "username" or "email" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        user = None

        if 'allauth' in settings.INSTALLED_APPS:
            from allauth.account import app_settings

            # Authentication through email
            if app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.EMAIL:
                user = self._validate_email(email, password)

            # Authentication through username
            if app_settings.AUTHENTICATION_METHOD == app_settings.AuthenticationMethod.USERNAME:
                user = self._validate_username(username, password)

            # Authentication through either username or email
            else:
                user = self._validate_username_email(username, email, password)

        else:
            # Authentication without using allauth
            if email:
                try:
                    username = UserModel.objects.get(email__iexact=email).get_username()
                except UserModel.DoesNotExist:
                    pass

            if username:
                user = self._validate_username_email(username, '', password)

        # Did we get back an active user?
        if user:
            if not user.is_active:
                msg = _('User account is disabled.')
                raise exceptions.ValidationError(msg)
        else:
            msg = _('Unable to log in with provided credentials.')
            raise exceptions.ValidationError(msg)

        # If required, is the email verified?
        if 'rest_auth.registration' in settings.INSTALLED_APPS:
            from allauth.account import app_settings
            if app_settings.EMAIL_VERIFICATION == app_settings.EmailVerificationMethod.MANDATORY:
                email_address = user.emailaddress_set.get(email=user.email)
                if not email_address.verified:
                    raise serializers.ValidationError(_('E-mail is not verified.'))

        attrs['user'] = user
        return attrs



# from profiles.payment.utils import *
class CustomTokenSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for Token model.
    """
    uid = serializers.SerializerMethodField(method_name = '_get_userid')

    def _get_userid(self, obj):
        u = obj.user
        return u.id

    class Meta:
        model = Token
        fields = ('key', 'uid')

class CustomPasswordResetSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset e-mail.
    """

    email = serializers.EmailField()

    password_reset_form_class = PasswordResetForm

    def validate_email(self, value):
        # Create PasswordResetForm with the serializer
        self.reset_form = self.password_reset_form_class(data=self.initial_data)
        if not self.reset_form.is_valid():
            raise serializers.ValidationError('Error')
        return value

    def save(self):
        request = self.context.get('request')
        # Set some values to trigger the send_email method.
        opts = {
            'use_https': request.is_secure(),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL'),
            'request': request,
            'email_template_name': 'profiles/password_reset_email.html',
            'subject_template_name': 'profiles/password_reset_subject.txt',
        }
        self.reset_form.save(**opts)

class CustomPasswordChangeSerializer(serializers.Serializer):

    old_password = serializers.CharField(max_length=128)
    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)

    set_password_form_class = SetPasswordForm

    def __init__(self, *args, **kwargs):
        self.old_password_field_enabled = getattr(
            settings, 'OLD_PASSWORD_FIELD_ENABLED', False
        )
        super(PasswordChangeSerializer, self).__init__(*args, **kwargs)

        if not self.old_password_field_enabled:
            self.fields.pop('old_password')

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    def validate_old_password(self, value):
        
        invalid_password_conditions = (
            self.old_password_field_enabled,
            self.user,
            not self.user.check_password(value)
        )

        if all(invalid_password_conditions):
            raise serializers.ValidationError('Invalid password')
        return value

    def validate(self, attrs):
        # Alan: possible to inject additional password requirements for security here.
        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs
        )

        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        return attrs

    def save(self):
        self.set_password_form.save()

class DisconnectSocialSerializer(serializers.Serializer):
    backend = serializers.CharField(max_length=20, required=True, allow_null= False)
    association_id = serializers.IntegerField(required = False, allow_null = True)


# view_names_base = {
#   # 'UserSearchSerializer' : 'usersearch',
#   'UserProfileSerializer' : 'userprofile',
#   'UserSerializer' : 'user',
#   'GroupSerializer': 'group',
#   'GroupMemberRelationSerializer': 'groupmemberrelation',
#   'GroupMemberRelationSimpleSerializer': 'groupmemberrelationsimple',
#   'GroupMemberRelationDashboardSerializer': 'groupmemberrelationdashboard',
#   # 'GroupMemberAsTraineeSerializer': 'groupmemberastrainee',
#   'SuperExpertExpertRelationSerializer': 'superexpertexpertrelation',
#   'SuperExpertExpertRelation_asSubExpert_Serializer': 'superexpertexpertrelation_assubexpert',
#   'SuperExpertExpertRelation_asSuperExpert_Serializer': 'superexpertexpertrelation_assuperexpert',
#   'TraineeExpertRelationSerializer':'traineeexpertrelation',
#   'TraineeExpertRelation_asExpert_Serializer': 'traineeexpertrelation_asexpert',
#   'TraineeExpertRelation_asTrainee_Serializer': 'traineeexpertrelation_astrainee',
#   'MeSerializer': 'me',
#   'InviteSerializer': 'invite',
#   'DisconnectSocialSerializer':'disconnectsocial',


# }


from allauth.account.models import EmailConfirmation
# plain model serializers above, complex ones on the bottom so they may refer to classes above


def get_model_concrete_fields(MyModel):
    return [
        f.name
        for f in MyModel._meta.get_fields()
        if f.concrete and (
            not f.is_relation
            or f.one_to_one
            or (f.many_to_one and f.related_model)
        )
    ]


class StudentResetPWSerializer(serializers.Serializer):
    password1 = serializers.CharField(max_length=200)
    password2 = serializers.CharField(max_length=200)
    uid = serializers.IntegerField()

    class Meta:
        model = User
        fields = ('password1' ,'password2', 'uid')
        extra_kwargs = {'password1': {'write_only': True}, 'password2': {'write_only': True}}

class StudentDeactivateSerializer(serializers.Serializer):
    uid = serializers.IntegerField()
    class Meta:
        fields = ('uid')


class UserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    username = serializers.CharField(max_length=200, required=False, allow_blank=True)
    password1 = serializers.CharField(max_length=200)
    password2 = serializers.CharField(max_length=200)
    role = serializers.CharField(max_length=1)
    verifyToken = serializers.CharField(max_length=200, required=False, allow_blank=True)
    isMyStudent = serializers.BooleanField(required = False)

    class Meta:
        model = User
        fields = ('email', 'username', 'password1' ,'password2', 'role')
        extra_kwargs = {'password1': {'write_only': True}, 'password2': {'write_only': True}}

class UserProfileSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(
    #     view_name='{}-detail'.format('userprofile'),
    # )

    # userURL = serializers.HyperlinkedIdentityField(
    #     view_name='{}-detail'.format(view_names_base['UserSerializer']),
    # )

    # # birth_date = serializers.DateTimeField(format=None, input_formats=None)

    # social = serializers.SerializerMethodField('_get_social_accounts')
    # devices = JSONSerializerField(default={}, required = False)
    # onboarding = JSONSerializerField(default={}, required = False)

    # default_ageModelHRThreshold = serializers.IntegerField(source='get_default_ageModelHRThreshold', read_only = True)


    # def _get_social_accounts(self, obj):
    #     return obj.social_auth.all().values('uid', 'provider', 'extra_data')

    class Meta:
        model = User
        fields = ('url', 'id', 'avatar_url', 'birth_date', 'gender', 'firstname', 'lastname', 'tzName', 'phoneNumber', 
            'location', 'lon', 'lat',
            'hasOnboarded',
            'isSearchable',
            'role',
            'school',

            # 'username', 
            'email', 
            
            )


from course.serializers import UserCourseRelationshipSerializer
class UserSerializer(serializers.HyperlinkedModelSerializer):
    # url = serializers.HyperlinkedIdentityField(
    #     view_name='{}-detail'.format(view_names_base['UserSerializer'])
    # )

    is_email_verified = serializers.SerializerMethodField(method_name = '_get_email_verification')

    enrolledCourses = serializers.SerializerMethodField(method_name = '_get_enrollment')

    # overkill with too much data
    # enrolledCourses = UserCourseRelationshipSerializer(
    #     many= True, 
    #     source = 'get_myEnrolledCourses',
    #     read_only= True
    #     )

    def _get_enrollment(self, obj):
        userCourses = self.get_myEnrolledCourses
        return [i.course for i in userCourses]


    def _get_email_verification(self, obj):
        ea = EmailAddress.objects.filter(user = obj)

        if ea.exists():
            return ea.first().verified

        return False


    class Meta:
        model = User
        fields = ('url', 'id' ,'name', 'email', 'role',

            'is_email_verified', 'location', 'avatar_url',
            'displayName',
            'username',
            'enrolledCourses',
            )

class UserSimpleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('name', 'avatar_url' )

class GuardianStudentRelationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GuardianStudentRelation
        # fields = '__all__' 
        fields = get_model_concrete_fields(model) + ['url']

class SchoolSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = School
        fields = get_model_concrete_fields(model) + ['url']

# class UserSchoolRelationSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = UserSchoolRelation
#         fields = get_model_concrete_fields(model) + ['url']
#         # fields = '__all__' 


class UserFileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserFile
        fields = get_model_concrete_fields(model) + ['url']
        # fields = '__all__' 


from uploadApp.serializers import ProjectSerializer
from course.serializers import TrophyRecordSerializer
class MeSerializer(serializers.HyperlinkedModelSerializer):

    # mySchools = SchoolSerializer(many= True, 
    #                         source = 'get_mySchools',
    #                         read_only= True)

    myStudents = UserSerializer(many= True, 
                            source = 'get_myActiveStudents',
                            read_only= True)

    myProjectsCount = serializers.IntegerField(
                        source='project_set.count', 
                        read_only=True
                    )

    myTrophyRecordsCount = serializers.IntegerField(
                        source='trophyrecord_set.count', 
                        read_only=True
                    )

    

    myReactionsCount = serializers.IntegerField(
                        source='get_myReactions.count', 
                        read_only=True
                    )


    isPasswordSet = serializers.SerializerMethodField(method_name = '_get_isPasswordSet')

    isEmailVerified = serializers.SerializerMethodField(method_name = '_get_email_verification')

    def _get_email_verification(self, obj):
        ea = EmailAddress.objects.filter(user = obj)

        if ea.exists():
            return ea.first().verified

        return False

    def _get_isPasswordSet(self, obj):
        if len(obj.password) > 0:
            return True
        return False


    class Meta:
        model = User
        fields = ('url', 'id', 'avatar_url', 'birth_date', 'gender', 'firstname', 'lastname', 'tzName', 'phoneNumber', 
            'location', 'lon', 'lat',
            'hasOnboarded',
            'isSearchable',
            'role',
            'school',

            # 'mySchools',
            'myStudents',
            'myProjectsCount',
            'myTrophyRecordsCount',
            'myReactionsCount',
            
            'username', 
            'email', 
            'displayName',
            'slugName',

            'isPasswordSet',
            'isEmailVerified',


        
            )
        read_only_fields = ()

