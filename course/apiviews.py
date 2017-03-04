from course.models import *
from course.serializers import *

from rest_framework import viewsets, filters, generics, views

import sys, inspect, itertools
from rest_framework.exceptions import APIException, ParseError, PermissionDenied
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from django.utils import timezone
from django.conf import settings

from .utils import get_model_concrete_fields

import requests

from dateutil.parser import parse as dateTimeParse

from rest_framework.settings import api_settings
from rest_framework_csv import renderers as r


class EnrollmentReportView(views.APIView):
    """
    yields report for the user
    """

    api_name = 'enrollmentreport'
    # queryset = UserCourseRelationship.getAllEnrollmentReport
    permission_classes = (IsAuthenticated,)
    renderer_classes = [r.CSVRenderer, ] + api_settings.DEFAULT_RENDERER_CLASSES
    http_method_names =['get']

    def get(self, request, *args, **kwargs):
        return Response(UserCourseRelationship.getAllEnrollmentReport())





class UserCourseRelationshipViewSet(viewsets.ModelViewSet):
    """
    defines the relationship between Instructor user and courses
    """
    api_name = 'usercourserelationship'
    queryset = UserCourseRelationship.objects.all()
    serializer_class = UserCourseRelationshipSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('user',)



class CourseViewSet(viewsets.ModelViewSet):
    """
    defines the Course objects 
    """
    api_name = 'course'
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (AllowAny,)

    http_method_names =['get']
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter,)
    filter_fields = ('course_code',)
    search_fields = ('course_code', 'name', 'location', 'id')


class CourseClassDateRelationship(viewsets.ModelViewSet):
    """
    defines the CourseClassDateRelationship objects 
    """
    api_name = 'courseclassdaterelationship'
    queryset = CourseClassDateRelationship.objects.all()
    serializer_class = CourseClassDateRelationshipSerializer
    http_method_names =['get']
    permission_classes = (AllowAny,)
    # filter_backends = (filters.DjangoFilterBackend,)
    # filter_fields = ('course_code',)


class LessonViewSet(viewsets.ModelViewSet):
    """
    defines the Course objects 
    """
    api_name = 'lesson'
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('course',)


class ChallengeViewSet(viewsets.ModelViewSet):
    """
    defines the School objects that could be associated with a user under UserSchoolRelation
    """
    api_name = 'challenge'
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('lesson',)


class TrophyViewSet(viewsets.ModelViewSet):
    """
    defines the School objects that could be associated with a user under UserSchoolRelation
    """
    api_name = 'trophy'
    queryset = Trophy.objects.all()
    serializer_class = TrophySerializer
    permission_classes = (IsAuthenticated,)


class ChallengeRecordViewSet(viewsets.ModelViewSet):
    """
    defines the Challenge records to denote the progress of the user in the challenges, also used in determining earned trophies
    """
    api_name = 'challengerecord'
    queryset = ChallengeRecord.objects.all()
    serializer_class = ChallengeRecordSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('user',)

class ChallengeProgressViewSet(viewsets.ModelViewSet):
    """
    defines the user's progress within a challenge which may have multiple questions. progress within a challenge is recognized by a signature
    \n the MD5 signature can be generated using a question's text for example
    """
    api_name = 'challengeprogress'
    queryset = ChallengeProgress.objects.all()
    serializer_class = ChallengeProgressSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('user', 'challenge')


class TrophyRecordViewSet(viewsets.ModelViewSet):
    """
    defines the School objects that could be associated with a user under UserSchoolRelation
    """
    api_name = 'trophyrecord'
    queryset = TrophyRecord.objects.all()
    serializer_class = TrophyRecordSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('user',)

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

class CodeNinjaCacheUpdateView(views.APIView):
    """
    \n POST to update CodeNinjaCache
    """
    api_name = 'codeninjacacheupdate'

    # this endpoint should be public so anyone can sign up
    permission_classes = (AllowAny, )
    http_method_names =['post']
    cnHeaders = {'Authorization': settings.CNKEY}
    
    def updateCourse(self, c, classDates = []):
        """
        suppose code ninja passes a payload of a course, update or create the records on nectar
        ie:
        c = {
          "name": "Playful Discovery of Robotics",
          "age_group": "6-8",
          "course_icon_url": "https://firstcode-codeninjas-v3.s3.amazonaws.com/hk/uploads/course_module/50/course_icon_url/icon_robotics.jpg",
          "course_code": "CC16-AT-RO-1219-SW",
          "location": "Sheung Wan",
          "start_date": "2016-12-19",
          "end_date": "2016-12-23",
          "start_time": "2000-01-01T10:00:00.000Z",
          "end_time": "2000-01-01T12:00:00.000Z",
          "capacity": 8,
          "enrollment_count": 5,
          "eventbrite_tag": "28953934999",
          "active": true,
          "remark": "5-day camp, 10 hours total."
        }

        """

        if c['course_code'] is None or len(c['course_code']) == 0:
            # skip items that are not valid
            return None, False

        # filter out certain keys that should not be overwritten
        c = {k:v for (k,v) in c.items() if k not in ['id'] and k in get_model_concrete_fields(Course) }

        # prevent null course_icon_url fields
        if 'course_icon_url' in c and c['course_icon_url'] is None:
            c['course_icon_url'] = ''

        course, created = Course.objects.update_or_create(
            # filter by
            course_code = c['course_code'],


            # name =  c['name'],
            # age_group = c['age_group'],
            # course_icon_url = c['course_icon_url'],
            # location = c['location'],
            # start_date = c['start_date'],
            # end_date = c['end_date'],
            # start_time = c['start_time'],
            # end_time = c['end_time'],
            # capacity = c['capacity'],
            # enrollment_count = c['enrollment_count'],
            # # eventbrite_tag = c['eventbrite_tag'],
            # active = c['active'],
            # remark = c['remark'],

            defaults = c,
        )

        # update course time info, but only for term courses because it requires the classDates param for this to be correct
        # camps and events have their class dates saved during model save, see models.py
        if course.event_type == 'term':
            course.updateClassDates(classDates)

        # print 'course created', course.id, created, course.course_code





        return course, created

    def processCamps(self, payload_ids, subdomain= None):
        """
        processes the returned data for camps
        """

        memo = {}

        for i in payload_ids:
            # attempt to poll data from 

            # r = requests.get('http://hk.firstcodeacademy.com/api/camps/3/offerings', headers=self.cnHeaders)
            # print r.json()

            obj = None

            # try:


            r = requests.get(i, headers=self.cnHeaders)
            data = r.json()

            # print i

            # filter out certain keys that should not be overwritten
            data = {k:v for (k,v) in data.items() if k not in ['id'] }

            obj, created = CodeNinjaCache.objects.update_or_create(
                # filter by this
                endpoint = i,

                # insert / update this
                defaults = { 'data': data },
            )

            # print obj, created, obj.data, obj.data.get('offerings', [])

            # camps have start / end dates lodged inside the course object
            # courseDates = obj.getCourseDates()


        
            if obj:
                for c in obj.data.get('offerings', []):

                    # inject subdomain to c
                    c['subdomain'] = subdomain

                    # print 'offering', c

                    if c['course_code'] not in memo:
                        c['cnType'] = 'camps'
                        self.updateCourse(c, classDates = [])
                    
                    memo[c['course_code']] = c



            # except Exception as e: 
            #     print 'CodeNinjaCacheUpdate', e, i




        return memo

    def processPrograms(self, payload_ids, subdomain = None):
        """
        processes the returned data for camps
        """

        memo = {}

        for i in payload_ids:
            # attempt to poll data from 

            # r = requests.get('http://hk.firstcodeacademy.com/api/camps/3/offerings', headers=self.cnHeaders)
            # print r.json()

            obj = None

            # let's not obscure errors
            # try:



            r = requests.get(i, headers=self.cnHeaders)
            data = r.json()

            # filter out certain keys that should not be overwritten
            data = {k:v for (k,v) in data.items() if k not in ['id'] }

            obj, created = CodeNinjaCache.objects.update_or_create(
                # filter by this
                endpoint = i,

                # insert / update this
                defaults = { 'data': data },
            )

            # programs have dates listed in class_dates field , extract them
            # courseDates are supplied as a dict of {<weekday>: [<datetime>...]}
            courseDates = obj.getCourseDates()


            weekdayMapping = {
                'mon': 0,
                'tue': 1,
                'wed': 2,
                'thu': 3,
                'fri': 4,
                'sat': 5,
                'sun': 6,
            }


        
            if obj:   
                for c in obj.data.get('offerings', []):
                    
                    # print 'offering', c

                    # inject subdomain to c
                    c['subdomain'] = subdomain

                    if c['course_code'] not in memo:
                        c['cnType'] = 'programs'

                        # courseDates are supplied as a dict of {<weekday>: [<datetime>...]}
                        # classDates only selects the time of date
                        classDates = []

                        # these are 'Mon', 'Tue'
                        class_day = c.get('class_day', '')

                        # is the translated numerical mapping as specified in weekdayMapping
                        class_weekday = weekdayMapping.get(class_day.lower(), None)
                        if class_weekday is not None:
                            classDates = courseDates.get(class_weekday, [])
                            # print 'extracted classDates', classDates


                        self.updateCourse(c, classDates = classDates)
                    
                    memo[c['course_code']] = c


            # except Exception as e: 
            #     print 'CodeNinjaCacheUpdate', e, i


        return memo

    def processEvents(self, activeEventsData_payloads, subdomain = None):
        """
        processes the returned data for camps
        """

        memo = {}

        for p in activeEventsData_payloads:
            # attempt to poll data from 

            # r = requests.get('http://hk.firstcodeacademy.com/api/camps/3/offerings', headers=self.cnHeaders)
            # print r.json()

            obj = None

            # let's not obscure errors
            # try:



            r = requests.get(p.get('url'), headers=self.cnHeaders)
            data = r.json()

            # filter out certain keys that should not be overwritten
            data = {k:v for (k,v) in data.items() if k not in ['id'] }




            obj, created = CodeNinjaCache.objects.update_or_create(
                # filter by this
                endpoint = i,

                # insert / update this
                defaults = { 'data': data },
            )

            if obj:   
                for c in obj.data.get('offerings', []):

                    # inject subdomain to c
                    c['subdomain'] = subdomain

                    # print 'offering', c

                    if c['course_code'] not in memo:
                        c['cnType'] = 'events'

                        # events have dates and some other fields injected in its parent call http://hk.firstcodeacademy.com/api/events/
                        # inject them to this child course
                        c['start_date'] = c['event_date']
                        c['end_date'] = c['event_date']

                        # this date from p is wrong, take the value from c
                        # c['start_time'] = p['start_time']
                        # c['end_time'] = p['end_time']

                        c['event_type'] = p['event_type']

                        # inject prices, which are all the same for the set of courses in this event
                        c['prices'] = obj.data.get('prices', [])
                        c['name'] = obj.data.get('name', '')

                        self.updateCourse(c, classDates = [])
                    
                    memo[c['course_code']] = c

        return memo

            











    def post(self, request, format=None, *args, **kwargs):
        verifyToken = request.data.get('verifyToken')

        # confirm that frontend has a signature passed
        if verifyToken != settings.VERIFYTOKEN:
            raise PermissionDenied('Verification Token missing or invalid')

        # needed for codeninja verification



        countriesUrl = 'https://www.firstcodeacademy.com/api/countries'
        # countriesUrl = 'https://www.google.com'
        r = requests.get(countriesUrl, headers = self.cnHeaders)

        # print r, r.status_code, r.text, self.cnHeaders

        countriesData = r.json()
        subdomains = [i['subdomain'] for i in countriesData]


        allcampsMemo = {}
        allprogramsMemo = {}
        alleventsMemo = {}



        for s in subdomains:

            # take a look at the active camps first
            activeCampsUrl = 'https://{}.firstcodeacademy.com/api/camps'.format(s)
            r = requests.get(activeCampsUrl, headers = self.cnHeaders)
            activeCampsData = r.json()

            activeCampsData_ids = ['https://{}.firstcodeacademy.com/api/camps/{}'.format(s ,i['id']) for i in activeCampsData]
            print 'activeCampsData_ids', activeCampsData_ids

            # now we can start polling endpoint
            campsMemo = self.processCamps(activeCampsData_ids, subdomain = s)
            for k in campsMemo:
                allcampsMemo[k] = campsMemo[k]




            # take a look at the programs
            activeProgramsUrl = 'https://{}.firstcodeacademy.com/api/programs'.format(s)
            r = requests.get(activeProgramsUrl, headers = self.cnHeaders)
            activeProgramsData = r.json()

            activeProgramsData_ids = ['https://{}.firstcodeacademy.com/api/programs/{}'.format(s, i['id']) for i in activeProgramsData]
            print 'activeProgramsData_ids', activeProgramsData_ids

            # now we can start polling endpoint
            # missing course_code, abort
            # programsMemo = None
            programsMemo = self.processPrograms(activeProgramsData_ids, subdomain = s)
            for k in programsMemo:
                allprogramsMemo[k] = programsMemo[k]


            # take a look at the events (which has all the trial classes)
            activeEventsUrl = 'https://{}.firstcodeacademy.com/api/events'.format(s)
            r = requests.get(activeEventsUrl, headers = self.cnHeaders)
            activeEventsData = r.json()


            activeEventsData_payloads = [
                { 
                    'url':'https://{}.firstcodeacademy.com/api/events/{}'.format(s, i['id']),
                    # the event_date field is not correct, look at the offerings instead
                    # 'start_date':  i['event_date'],
                    # 'end_date':  i['event_date'],
                    'start_time': i['start_time'],
                    'end_time': i['end_time'],
                    'event_type': i['event_type'],

                } for i in activeEventsData

            ]
            print 'activeEventsData_payloads', activeEventsData_payloads

            # now we can start polling endpoint
            # missing course_code, abort
            # eventsMemo = None
            eventsMemo = self.processEvents(activeEventsData_payloads, subdomain = s, )
            for k in eventsMemo:
                alleventsMemo[k] = eventsMemo[k]



        allActiveCourse_codesMemo = set(allcampsMemo.keys()).union(allprogramsMemo.keys()).union(alleventsMemo.keys())  

        # set the courses across the board
        Course.setActiveCourses(allActiveCourse_codesMemo)




        r = {'status': 'success', 
        'campsMemo': allcampsMemo, 
        'programsMemo': allprogramsMemo,
        'eventsMemo': alleventsMemo,

        }

        return Response(r)


    
clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
clsmembers = filter(lambda x: issubclass(x[1], viewsets.ModelViewSet )  \
                    or issubclass(x[1], viewsets.ReadOnlyModelViewSet ) \
                    or issubclass(x[1], views.APIView ) \
                    # or issubclass(x[1], CreateAPIView ) \
                    , clsmembers)
