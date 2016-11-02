from django.utils import timezone
from django.db.models import Count
from django.db.models import Avg, Count, F, Max, Min, Sum, Q, Prefetch

# this files houses all the metrics calculations on the dashboard of an expert
# i.e. tracking logins, adherence to workout (Rhythm), social loudness ... etc


def get_viewingUserOrNone(self):
  viewingUser = None
  request = self.context.get("request")
  if request and hasattr(request, "user"):
      viewingUser = request.user

  return viewingUser

def get_notification_list(self, targetUser):
  """
  this should get the topic notiifications of the viewingUser 
  on the individual stream of the targetUser as if he's a one on one trainee
  """

  viewingUser = get_viewingUserOrNone(self)
  if not viewingUser:
    return []


  r = viewingUser.topicnotification_set.filter( 
                                      # is_active = True, 
                                      is_read = False, 
                                      topic__topicUserRelation__user = targetUser
                                      )
  
  return r.values_list('id', 'topic_id')


def get_group_notification_list(self, targetUser, targetGroup):
  """
  this should get the topic notiifications of the viewingUser on the group stream
  filtered by the targetUser as author of the comment or topic message
  """
  author = targetUser

  viewingUser = get_viewingUserOrNone(self)
  if not viewingUser:
      return []



  r = author.topicnotification_set.model.objects.filter(
      Q(topic__user = author) | Q(comment__user = author),
      user = viewingUser, 
      # is_active = True, 
      is_read = False, 
      topic__topicGroupRelation__group = targetGroup
      ).values('id', 'topic_id', 'comment_id')

  r_clean = []
  for i in r:
      r_clean.append([i['id'], i['topic_id']])



  return r_clean

def get_group_total_notification_list(self, targetGroup):
    """
    this should get the topic notiifications of the viewingUser on the group stream
    filtered by the member as author of the comment or topic message
    """

    viewingUser = get_viewingUserOrNone(self)
    if not viewingUser:
        return []

    r = viewingUser.topicnotification_set.filter(
                                        # user = viewingUser, 
                                        # is_active = True, 
                                        is_read = False, 
                                        topic__topicGroupRelation__group = targetGroup
                                        )
    return r.values_list('id', 'topic_id')


def get_days_workout_left(targetUser ):
    """
    get the number of days of workout left in the trainee's calendar
    """
    # targetUser = obj.user
    today = timezone.now().date()
    # print 'today', today

    uac = targetUser.UserActivityCalendar_user.filter(
        assignedDate__gte = today
        ).values('assignedDate').distinct().order_by('assignedDate')

    d_list = [i['assignedDate'] for i in uac]
    # print d_list



    c_date = today
    c = 0
    for d in d_list:
        if c_date != d.date():
            break

        # print 'matching', c_date
        c_date += timezone.timedelta(days = 1) 
        c += 1

    return c

def get_group_days_workout_left(targetGroup):
    """
    get the number of days of workout left in the group's calendar
    """

    today = timezone.now().date()
    # print 'today', today

    gac = targetGroup.GroupActivityCalendar.filter(
        # group = targetGroup, 
        assignedDate__gte = today
        ).values('assignedDate').distinct().order_by('assignedDate')

    d_list = [i['assignedDate'] for i in gac]
    # print d_list

    c_date = today
    c = 0
    for d in d_list:
        if c_date != d.date():
            break

        # print 'matching', c_date
        c_date += timezone.timedelta(days = 1) 
        c += 1

    return c


def get_new_pr(self, targetUser):
    """
    gets the personal record of all time best peaks for cycling/running/swimming of the trainee / user
    when they are set, the user activity calendar goes gold
    the PR can only be dismissed by viewing the Calendar itself.
    """

    viewingUser = get_viewingUserOrNone(self)
    if not viewingUser:
      return 0

    now = timezone.now()
    lag_dt = now - timezone.timedelta(days = 14)

    cps = viewingUser.cpnotification.filter(
        # user = viewingUser, 
        activitySummaryData__user = targetUser,
        is_read = False,
        # obsDate__lte = now,
        # obsDate__gte = lag_dt,
         ).count()

    return cps


def get_last_login(targetUser):
  """
  gets the last count of logins in the last 14 days, multiple logins in the same day count as 1.
  when user loads me/ it counts as an act of loggin in.
  user login use user profile as login record storage
  """
  log = targetUser.login_log

  if not isinstance(log, list):
      return 0

  return len(set(log))

def get_response_count(targetUser):
  """
  gets the number of activities responded by user in the last 14 days. 
  if there were 30 activities all responded, this will say 30
  """


  # beginning time is 14 days ago
  begTime = timezone.now() - timezone.timedelta(14)
  uac = targetUser.UserActivityCalendar_user.filter(
    # user = obj.user, 
    assignedDate__gte = begTime , 
    assignedDate__lte = timezone.now() 
    ).values('AthleteResponse')

  return sum(1 if i['AthleteResponse'] is not None else 0 for i in uac)


def get_groups_with_plans(targetUser):
    """
    returns groups only that has plans in them, for calnedar display purposes
    - will only return groups with more than one cycle
    """
    # user = obj.user
    q = targetUser.GroupMemberRelation.values('group').annotate(Count('group__GroupPlanCalendar__GroupCycleCalendar')).filter(
        group__GroupPlanCalendar__GroupCycleCalendar__count__gt = 0,
        is_admin = False)
    # user.
    return [i['group'] for i in q ]



def get_rhythm(targetUser):
  """
  looks at a user's completed (or UserActvivtyCalendar (UAC) that has data) vs. 
  UAC that are not completed in last "n" days 
  """

  now = timezone.now()
  # short term measurement duration, set to 7 days
  sht_from = now - timezone.timedelta(days = 7)

  # long term duration, set to 6 weeks
  lng_from = now - timezone.timedelta(weeks = 6)

  r = {
    'sht': 0,
    'lng': 0,
  }

  all_uac = targetUser.UserActivityCalendar_user.filter(
    assignedDate__lte = now
    )
  if all_uac.count() == 0:
    return r

  uac_sht = targetUser.UserActivityCalendar_user.annotate(Count('ActivitySummaryData')).filter(
    # Q(is_Complete = True) | Q(ActivitySummaryData__count__gt = 0), 
    assignedDate__gte = sht_from,
    assignedDate__lte = now
  ).values(
    'ActivitySummaryData__count',
    'is_Complete',
    )

  if len(uac_sht) > 0:
    r['sht'] = len(filter(lambda x: x['ActivitySummaryData__count'] > 0 or x['is_Complete'] == True, uac_sht))
    r['sht'] = float(r['sht']) / len(uac_sht)

  uac_lng = targetUser.UserActivityCalendar_user.annotate(Count('ActivitySummaryData')).filter(
    # Q(is_Complete = True) | Q(ActivitySummaryData__count__gt = 0), 
    assignedDate__gte = lng_from,
    assignedDate__lte = now
  ).values(
    'ActivitySummaryData__count',
    'is_Complete',
    )

  if len(uac_lng) > 0:
    r['lng'] = len(filter(lambda x: x['ActivitySummaryData__count'] > 0 or x['is_Complete'] == True, uac_lng))
    r['lng'] = float(r['lng']) / len(uac_lng)
    
  return r


def get_asdWithStress(targetUser, d = 42):
  """
  looks at target user and determins how many days in the last d days does this user:
  - have filedata for which a stress can be calculated
  """
  u = targetUser
  c = 0
  for i in u.ActivitySummaryData.filter(
    activityStartDateTime__gte = timezone.now() - timezone.timedelta(days = d)
  ):
      if round(i.get_stress()) != 0.0:
          c += 1

  return c







