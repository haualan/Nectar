# internal scripts
from sccalendar.models import PlanTemplate
from django.utils import timezone
from pprint import pprint
import copy



def displacePlanTemplate(p, d, update = False):
  """
  p is the plantemplate object, d is the day shift applied to the activities within
  - because all the plan contents have been displaced by 1 day, there needs to be some way to correct this
  - prior to 06072016 all activities inside plan templates were incorrect
  """

  # all plan startdates should really be at 12-28-2016
  static_pdt = timezone.datetime(2016,12,28).date()
  pdt = timezone.datetime(2016,12,28).date()
  # pdt = p.assignedDate.date()

  # these are all the cycles of the plan

  c = copy.deepcopy(p.cycles)

  # store the current dates for each activity in a list
  a_list = []

  # for each week in a cycle...
  c_weeks = 0
  for cycle in c:
    for weekCount, week in enumerate(cycle['weeks']):
      for dayCount, day in enumerate(week['days']):
        # pprint(day)
        # day only contains a list of  activities
        # for a in day:
          # print a
        print dayCount, weekCount + c_weeks, pdt + timezone.timedelta(days = dayCount, weeks = weekCount + c_weeks)
        a_list.append({
          'assignedDate': pdt + timezone.timedelta(days = dayCount, weeks = weekCount + c_weeks),
          'day': day 
        })
      #   pdt += timezone.timedelta(days = 1)
      # pdt += timezone.timedelta(weeks = 1)
    # accumulated weeks for this cycle
    c_weeks += len(cycle['weeks'])

  # print 'before modify'
  # for j in a_list:
  #   print j['assignedDate']

  # shift the dates by datecount d and apply
  for i in a_list:
    # only modify date if it is greater than plan start date
    if i['assignedDate'] > static_pdt:
      i['assignedDate'] += timezone.timedelta(d)
    else:
      i['assignedDate'] = pdt

    if 'activities' in i['day']:
      for ao in i['day']['activities']:
        ao['assignedDate'] = i['assignedDate'].isoformat() + 'T00:00:00Z'

  # print 'after modify'
  # for j in a_list:
  #   print j['assignedDate']

  # print 'merge first 2 items, same date'
  f_a_list = mergeDays(filter(lambda x: x['assignedDate'] <= pdt, a_list))

  l_a_list = filter(lambda x: x['assignedDate'] > pdt, a_list)

  a_list = f_a_list + l_a_list
  # print a_list[0:3]

  # print 'after merge'
  # for j in a_list:
  #   print j['assignedDate']



  # reset pdt back to 12-28-2016
  pdt = timezone.datetime(2016,12,28).date()
  # assemble a_list back into a valid cycle: nc, now a copy of c
  nc = copy.deepcopy(c)
  c_weeks = 0
  for cycle in nc:
    for weekCount, week in enumerate(cycle['weeks']):
      # put in blank days
      week['days'] = [{},{},{},{},{},{},{}]
      for dayCount, day in enumerate(week['days']):

        # skip the day if there is no more to add
        if len(a_list) == 0:
          continue

        # day only contains a list of activities
        print a_list[0]['assignedDate'], pdt + timezone.timedelta(days = dayCount, weeks = weekCount + c_weeks ), dayCount, weekCount + c_weeks

        if a_list[0]['assignedDate'] == pdt + timezone.timedelta(days = dayCount, weeks = weekCount + c_weeks ):
          print 'pop a_list'
          v = a_list.pop(0)
          week['days'][dayCount] = v['day']
        
      #   pdt += timezone.timedelta(days = 1)
      # pdt += timezone.timedelta(weeks = 1)
    c_weeks += len(cycle['weeks'])

  # if after looping all there is still activities unadded we need to insert them to a new week
  # probably won't happend if d is negative
  if len(a_list) != 0:
    print 'lost activities'
    print a_list

  print 'new cycles'
  pprint(nc)

  if update == True:
    PlanTemplate.objects.filter(id = p.id).update(assignedDate = pdt, cycles = nc)

  return pdt, nc

def mergeDays(lod):
  """
  given a list of days payload, merge all activities within
  """
  pdt = timezone.datetime(2016,12,28).date()

  if len(lod) == 0:
    return []

  r = {}
  for i in lod:
    if 'activities' in i['day']:
      if 'activities' not in r:
        r['activities'] = []

      r['activities'] += i['day']['activities']

  return [{
    'assignedDate': pdt,
    'day': r
  }]
