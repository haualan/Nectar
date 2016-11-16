from django.http import HttpRequest
from django.conf import settings

try:
    from allauth.account import app_settings as allauth_settings
    from allauth.utils import (email_address_exists,
                               get_username_max_length)
    from allauth.account.adapter import get_adapter
    from allauth.account.utils import setup_user_email, send_email_confirmation
except ImportError:
    raise ImportError('allauth needs to be added to INSTALLED_APPS.')

from allauth.account.models import EmailAddress, EmailConfirmation
from rest_framework.authtoken.models import Token

from rest_framework import serializers
from requests.exceptions import HTTPError
from django.contrib.auth import get_user_model
# Import is needed only if we are using social login, in which
# case the allauth.socialaccount will be declared
# try:
#     from allauth.socialaccount.helpers import complete_social_login
# except ImportError:
#     raise ImportError('allauth.socialaccount needs to be installed.')

# if 'allauth.socialaccount' not in settings.INSTALLED_APPS:
#     raise ImportError('allauth.socialaccount needs to be added to INSTALLED_APPS.')


from profiles.models import User
class InviteSerializer(serializers.Serializer):

    email = serializers.EmailField(required=allauth_settings.EMAIL_REQUIRED)
    # group = serializers.CharField(max_length=8000 ,required=False, write_only=True)
    # expertUser = serializers.CharField(max_length=8000 ,required=False, write_only=True)
    name = serializers.CharField(required=False, write_only=True, max_length=100, allow_blank=True, default="")

    # flick to False is this is a resend
    isNewUser = True

    def validate_username(self, username):
        username = get_adapter().clean_username(username)
        return username

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            # if email and email_address_exists(email):
            if email and User.objects.filter(email = email):
                # redirect existing user to resend invitation link instead
                self.isNewUser = False
                return email
                # raise serializers.ValidationError(
                #     "A user is already registered with this e-mail address.")
        return email

    def validate_password1(self, password):
        return get_adapter().clean_password(password)

    # def validate_group(self, group):
    #     # if it's not string separated, then raise error
    #     try:
    #         group = [int(i) for i in group.split(',')]
    #     except:
    #         raise serializers.ValidationError("invalid group entry; must be comma separated values")

    #     for i in group:
    #         if not Group.objects.filter(id = i).exists():
    #             raise serializers.ValidationError("invalid group id: {} does not exist".format(i))
        
    #     return group

    # def validate_expertUser(self, expertUser):
    #     # if it's not string separated, then raise error
    #     try:
    #         expertUser = [int(i) for i in expertUser.split(',')]
    #     except:
    #         raise serializers.ValidationError("invalid expertUser entry; must be comma separated values")

    #     for i in expertUser:
    #         if not User.objects.filter(id = i).exists():
    #             raise serializers.ValidationError("invalid expertUser id: {} does not exist".format(i))
        
    #     return expertUser

    def custom_signup(self, request, user):
        # look for group payload and process as necessary

        # group = self.validated_data.get('group', None)
        # # print 'group entry', group
        # if group:
        #     for i in group:
        #         print 'user:', user.email, 'added to group', i
        #         user.add_to_group(i)

        # expertUser = self.validated_data.get('expertUser', None)
        # # print 'expertUser entry', expertUser
        # if expertUser:
        #     for i in expertUser:
        #         print 'user:', user.email, 'added expert', i
        #         user.add_expert(i)

        # name = self.validated_data.get('name', None)
        # if name:
        #     print 'user:', user.email, 'added name', name
        #     user.name = name
        #     user.save()


        # generate default running zone for new user assuming 11 min / mi pace
        # see setRunningZone method for defaults
        # user.setRunningZone()


        # generate link from branch io
        # inviteLink = 

        # send user confirmation email
        # but email will not resend if user is confirmed already, weird
        print 'InviteSerializer, send_email_confirmation for', user, user.id
        # send_email_confirmation(request._request, user, signup=True)


        # grab email address set of this user, if it doesn't exist, create one
        ea, _ = user.emailaddress_set.update_or_create(email = user.email, defaults = {'verified': False, 'primary': True})

        # create a new ec to guarantee a new key
        ec = EmailConfirmation.create(ea)
        ec.send( signup=True)
        


    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', '')
        }

    def save(self, request):
        print 'CustomRegisterSerializer save triggered'

        # only perform these steps if we have a completely new user
        if self.isNewUser:
            adapter = get_adapter()
            user = adapter.new_user(request)
            self.cleaned_data = self.get_cleaned_data()
            adapter.save_user(request, user, self)
            
            setup_user_email(request, user, [])
        else:
            user = get_user_model().objects.get(email = self.validated_data.get('email'))


        self.custom_signup(request, user)


        return user
