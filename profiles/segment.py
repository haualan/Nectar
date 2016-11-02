from django.conf import settings
from rest_framework.exceptions import APIException, ParseError, PermissionDenied
from profiles.serializers import MeSerializer

import analytics
analytics.write_key = settings.SEGMENT_KEY

from threading import Thread
def postpone(function):
  def decorator(*args, **kwargs):
    t = Thread(target = function, args=args, kwargs=kwargs)
    t.daemon = True
    t.start()
  return decorator




@postpone
def getSegment(request, op):
  if op == 'identify':
    print 'identify segment'

    serializer = MeSerializer(request.user, context={'request': request})
    meData = serializer.data

    # p is the payload
    p = {}
    u = request.user

    p['name'] = u.email
    if u.name is not None and len(u.name) > 0:
        p['name'] = u.name

    p['email'] = u.email
    p['createdAt'] = u.date_joined

    myExpertNames = []
    for i in meData['myExperts']:
        myExpertNames.append(i['expertUser']['name'])

    # @kristo make this a csv string
    # https://trello.com/c/IssOpGTK/471-update-myexpertnames-on-backend-to-a-string-instead-of-an-array-consider-mobile-implications
    myExpertNames = ", ".join(myExpertNames)


    # print meData

    p.update({
        'phone': meData['phoneNumber'],


        # // days of workout left, if negative, indicates days passed without workout
        'workoutsRemaining': meData['days_workout_left'],

        # // myExpertNames, my expert's names
        'myExpertNames': myExpertNames,


        'numberOfAthletes': len(meData['myTrainees']),
        # // iOSInstalled: '',


        'numberOfGroups': len(meData['myGroups']),


        # // number of plan templates in their library
        'planTemplates': meData['myPlanTemplateCount'],

        # // number of activity templates in their library
        'activityTemplates': meData['myActivityTemplateCount'],



        # // count of activitySummaryData
        'activityFiles': meData['myActivitySummaryDataCount'],

        # // onboarding link, for users who need help onboarding again
        'onboardingLink': meData['onboardingLink'],
        'isCoach': meData['isCoach'],
    })


    # // inject social stuff

    if 'social' in meData:
        for i in meData['social']:
            p[i['provider']] = i['uid'] 
        
    print p

    analytics.identify(request.user.id, p)

    return

  if op == 'track':
    print 'track segment'
    # analytics.track(request.user.id, {
    #   'email': 'john@example.com',
    #   'name': 'John Smith',
    #   'friends': 30
    # })
    return

  raise ParseError("query param op Unrecognized: {}, see API browser for details".format(op))
