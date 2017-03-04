from profiles.models import *
from django.utils import timezone
from course.models import internalEmailExclusionRegex



def guardiansPendingPurchase(request):
  """
  finds all users (that are guardians) who has registered but hasn't made a purchase in the system
  - the idea behind this is that a buyer landed on the page, looking to pay but might be deterred from making actual payment what gives...
  - so, users in this state can be collected and tracked, so FCA can act upon them

  """

  buyerUserIDs = Ledger.objects.all().distinct('buyerID').annotate(user_id = Cast('buyerID', IntegerField()))

  # users registered within this window but hasn't made a purchase
  detectionWindowHours = 24.0

  # only consider users joined within this window
  longWindowDays = 7 

  now = timezone.now()

  r = User.objects.filter(
    date_joined__gte = now - timezone.timedelta(days = longWindowDays),
    role = 'G',
  ).exclude( 
    id__in = buyerUserIDs
  ).exclude(
    email__regex  = internalEmailExclusionRegex,
  )

  results = [
    {
      'hoursWithoutPurchase': (now - u.date_joined).total_seconds() / 3600.0,
      'guardianEmail': u.email,
      'guardianPhone': u.phoneNumber,
      'guardianAddress': u.address,

    }
    for u in r if (((now - u.date_joined).total_seconds() / 3600.0) >= detectionWindowHours)
  ]


