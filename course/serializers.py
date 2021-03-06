
from course.models import *

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

from profiles.serializers import UserSimpleSerializer




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



class CourseCapacitySerializer(serializers.Serializer):
    course_code = serializers.CharField(max_length=200, required=True, allow_blank=False)

class CourseClassDateRelationshipSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CourseClassDateRelationship
        # fields = ['id']
        fields = get_model_concrete_fields(model) + ['url']

class CourseSerializer(serializers.HyperlinkedModelSerializer):
    # classDates = CourseClassDateRelationshipSerializer(source='courseclassdaterelationship_set'
    #     )

    classDates = CourseClassDateRelationshipSerializer(many=True, source = 'courseclassdaterelationship_set')

    # classDates = 

    class Meta:
        model = Course
        fields = get_model_concrete_fields(model) + ['url', 
            'classDates',
            # 'courseclassdaterelationship_set',
        ]


class LessonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Lesson
        fields = get_model_concrete_fields(model) + ['url']


class UserCourseRelationshipCreateSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserCourseRelationship
        fields = get_model_concrete_fields(model) + ['url']


class UserCourseRelationshipSerializer(serializers.HyperlinkedModelSerializer):
    course = CourseSerializer()
    user = UserSimpleSerializer()
    class Meta:
        model = UserCourseRelationship
        fields = get_model_concrete_fields(model) + ['url']


class ChallengeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Challenge
        fields = get_model_concrete_fields(model) + ['url']


class TrophySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Trophy
        fields = get_model_concrete_fields(model) + ['url']


class ChallengeRecordSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ChallengeRecord
        fields = get_model_concrete_fields(model) + ['url']

class ChallengeProgressSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ChallengeProgress
        fields = get_model_concrete_fields(model) + ['url']

class TrophyRecordSerializer(serializers.HyperlinkedModelSerializer):
    trophy = TrophySerializer()
    class Meta:
        model = TrophyRecord
        fields = get_model_concrete_fields(model) + ['url']
        # fields = ['createdDate', 'trophy', 'user', 'url']
