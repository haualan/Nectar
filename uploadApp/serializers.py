
from .models import *
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


from profiles.serializers import UserFileSerializer

# class ProjectScreenshotSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = ProjectScreenshot
#         # fields = '__all__' 
#         fields = get_model_concrete_fields(model) + ['url']

# class ProjectPackageFileSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = ProjectPackageFile
#         # fields = '__all__' 
#         fields = get_model_concrete_fields(model) + ['url']

# class ProjectIconFileSerializer(serializers.HyperlinkedModelSerializer):
#     userFileDetail = UserFileSerializer(
#         many = False,
#         source = 'userFile',
#         allow_null = True,
#         required = False,
#         read_only= True,
#         )

#     class Meta:
#         model = ProjectIconFile
#         # fields = '__all__' 
#         fields = get_model_concrete_fields(model) + ['url', 'userFileDetail']

class ProjectSourceFileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ProjectSourceFile
        # fields = '__all__' 
        fields = get_model_concrete_fields(model) + ['url', 'userFileDetail']


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    # projectIconFiles = ProjectIconFileSerializer(
    #     many = True,
    #     source = 'projecticonfile_set',
    #     allow_null = True,
    #     required = False
    #     )

    # projectScreenshots = ProjectScreenshotSerializer(
    #     many = True,
    #     source = 'projectscreenshot_set',
    #     allow_null = True,
    #     required = False
    #     )

    # projectPackageFiles = ProjectPackageFileSerializer(
    #     many = True,
    #     source = 'projectpackagefile_set',
    #     allow_null = True,
    #     required = False
    #     )

    projectSourceFiles = ProjectSourceFileSerializer(
        many = True,
        source = 'projectsourcefile_set',
        allow_null = True,
        required = False
        )
    class Meta:
        model = Project
        # fields = '__all__' 
        fields = get_model_concrete_fields(model) + ['url', 
        # 'projectIconFiles', 
        # 'projectScreenshots', 
        # 'projectPackageFiles', 
        'projectSourceFiles',
        ]

