import braintree, datetime
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
# from profiles.models import Group, GroupMemberRelation, TraineeExpertRelation, Payment, Organization, OrganizationAuditTrail, ORG_TRAINEE, ORG_EXPERT, ORG_GROUPMEMBER

# print 'braintree',braintree

braintree.Configuration.configure(braintree.Environment.Sandbox,
                                  merchant_id=settings.BRAINTREE_MERCHANT_ID,
                                  public_key=settings.BRAINTREE_PUB_KEY,
                                  private_key=settings.BRAINTREE_PRIV_KEY)

# def generate_payment_token(user):

#   customer = customer_create_or_update(user)
#   # print 'gen token', customer, customer.id
#   return braintree.ClientToken.generate({
#     "customer_id": customer.id
#     }), customer


# def customer_update(user, p_id):
#   """
#   updates user attr on braintree's side, but need to verify if customer exists first
#   """
#   # try split fname lname
#   fname = user.name.split(' ')[0]
#   lname = user.name.split(' ')[-1]

#   braintree.Customer.update(p_id, {
#     "first_name": fname,
#     "last_name": lname,
#     "email": user.email,
#     "phone": user.phoneNumber,
#   })






# def customer_create_or_update(user):
#   # try split fname lname
#   fname = user.name.split(' ')[0]
#   lname = user.name.split(' ')[-1]


#   p = user.Payment.first()

#   customer = None
#   if p:
#       # if braintree customer ID does exist, verify if it exists on braintree server
#       p_id = p.cust_id
#       try:
#           customer = braintree.Customer.find(p_id)

#           # update customer attributes on braintree side
#           customer_update(user, p_id)

#       except braintree.exceptions.not_found_error.NotFoundError as e:
#           print e
#           print 'create new braintree user'
#           customer = None

#   if customer is None:
#       # create the customer on braintree's end if it does not exist


#       result = braintree.Customer.create({
#           "id": user.id,
#           "first_name": fname,
#           "last_name": lname,
#           "email": user.email,
#           "phone": user.phoneNumber,
#           # "fax": "614.555.5678",
#           # "website": "www.example.com"
#       })

#       print 'braintree customer creation success?:', result.is_success
#       # True

#       # between stg and app /live server, test users with same ID might exist in sandbox 
#       # and not in production env. Detect if braintree is not allowing user retrieval that this is due to user being already created
#       if result.is_success == False :
#         de = result.errors.deep_errors
#         if '91609' in [i.code for i in de]:
#           # if error is due to duplicated user creation, get user from braintree again
#           customer = braintree.Customer.find(str(user.id))
#           customer_update(user, str(user.id))

#       else:
#         customer = result.customer

#   # e.g. 594019

#   # create or update the cust id for this user
#   user.Payment.update_or_create(defaults = {'cust_id': customer.id} )

#   return customer

# import itertools
# def has_active_sub(user, customer=None):
#   """
#   sees if user has active or pending subscription, 
#   indicating that user should still be able to login

#   Should not be used alone, because it's not able to detect if user is internal or staff or institutionally linked
#   """

#   if customer is None:
#     customer = customer_create_or_update(user)

#   subs = map(lambda x: x.subscriptions ,customer.payment_methods)
#   # print len(subs)

#   # flatten subs
#   subs = list(itertools.chain(*subs))
#   # print len(subs), [i.id for i in subs]

#   # filter subscrciptions that are active, pending, or pastdue
#   subs = filter(lambda x: x.status in [        
#     braintree.Subscription.Status.Active,
#     # braintree.Subscription.Status.Canceled,
#     # braintree.Subscription.Status.Expired,
#     # braintree.Subscription.Status.PastDue,
#     braintree.Subscription.Status.Pending
#     ], subs )

  
#   # determin result
#   r =  False
#   if len(subs) > 0:
#     r = True
  

#   if user is None :
#     try:
#       user = get_user_model().objects.filter(id = customer.id)
#     except:
#       user = None

#   if user:
#     p = Payment.objects.update_or_create(
#       user = user,
#       defaults = {
#         'cust_id': customer.id,
#         'hasActiveSub': r
#       }
#     )
#   else:
#     print 'braintree customer id:', customer.id, 'does not exist in sixcycle'

#   return r



# def syncCustomers():
#   """
#   Sync customer subscription stats with braintree
#   - since we use user ID to record customers in braintree, we just need to collect all their payment status info
#   - and update Payments table accordingly

#   """
#   all_cust = braintree.Customer.all()

#   # [(<user_id>,<hasActivePlan>)]
#   # calling has_active_sub would have overwriiten the user payment schedule
#   r = map( lambda c: (c.id ,has_active_sub(user = None, customer = c )), all_cust)

#   return r



# def validatePayWall(u, allCoachedGroups_ids = None):
#   """
#   given a user <u>, return True or False on whether user should be shown the paywall.
#   - does not actually change the Payment Table, only returns a boolean, change table accordingly
#   """

#   # does user have active sub?, init variable
#   hasActiveSub = False

#   # does the individual pay? init var
#   indivPay = True

#   # is user in trial?
#   isTrial = False
#   if u.date_joined + datetime.timedelta(days = settings.TRIAL_DAYS_COUNT) > timezone.now():
#     return False
#     # isTrial = True
#     # hidePayWall_list.append(u.id)
#     # continue

#   # init braintree customer
#   customer = None

#   # look at mapping table for braintree customer ID
#   p = u.Payment.first()

#   # this is only used if we don't trac subscription status, but we do now and we should...
#   # if p:
#   #   # if braintree customer ID does exist, verify if it exists on braintree server
#   #   p_id = p.cust_id
#   #   try:
#   #     customer = braintree.Customer.find(p_id)
#   #   except braintree.exceptions.not_found_error.NotFoundError as e:
#   #     # if it's not found, the user definitely does not have an active subscription
#   #     customer = None
#   #     hasActiveSub = False

#   # if customer:
#   #   # if braintree customer does exist, update their customer attributes, update their customer attributes and see if user has active subscripton

#   #   # update customer attr on braintree side
#   #   customer_update(u, p_id)

#   #   # see if customer has active sub
#   #   hasActiveSub = has_active_sub(u, customer=customer)

#   if p:
#     hasActiveSub = p.hasActiveSub


#   if u.isCoach:
#     # if the user is a coach, count how many trainees s/he has
#     # grab all trainees of this user
#     traineesCount = u.TraineeExpertRelation_trainee.all().count()

#     if traineesCount > 0:

#       # what organization is coach affiliated with?
#       # if coaching user is affiliated with an org, the org usually pays separately and the coach individually does not pay
#       # all non-standard payment methods for example : tiered pricing, coach-paying for all ... etc

#       # except if organization has isOrgPaying == False, in which case the org is just a container to group all the coaches. 
#       # all entities will still pay for themselves

#       try:
#         org = u.OrgRelationship.organization
#       except:
#         org = None

#       if org is not None and org.isOrgPaying == True:
#         # the individual pays nothing, org pays for user
#         indivPay = False
      
#       else:
#         # coaches pay for themselves, their trainees pay for themselves
#         indivPay = True

#     else:
#       # if this coach has no trainees, her account remains free
#       indivPay = False


#   else:
#     # user is regular athlete
#     # grab all experts of this user
#     totalExperts = u.TraineeExpertRelation_trainee.all()

#     payingExperts = u.TraineeExpertRelation_trainee.filter(
#       expertUser__OrgRelationship__isnull = False, 
#       expertUser__OrgRelationship__organization__isOrgPaying = True)

#     # print u.id, payingExpertsCount

#     if payingExperts.count() > 0:
#       # and some of the experts pay on their behalf then...
#       indivPay = False
    

#     # regardless if user still has to pay individually, check if user is a member of a coached group
#     # if there is a paying one on one coach, indivPay is switched to False. 
#     #   if user has other paying coach groups, he doesn't have to pay already, indivPay is set to False again
#     #   if user has no groups or non-coaching groups, the payingCoachedGroup.count() == 0 and indivPay is still False from before

#     # if trainee pays for himself, indivPay is true
#     #   look at coach paying groups, if he is a member of these groups, then his indivPay is False
#     #   if user has no groups or non-coaching groups, the payingCoachedGroup.count() == 0 and indivPay is still True from before

#     totalCoachedGroups = u.GroupMemberRelation.filter( 
#       group = Group.objects.filter(
#         GroupMemberRelation__isGroupCoach = True
#         )
#       )

#     payingCoachedGroups = u.GroupMemberRelation.filter( 
#       group = Group.objects.filter(
#         GroupMemberRelation__isGroupCoach = True, 
#         GroupMemberRelation__user__OrgRelationship__isnull = False,
#         GroupMemberRelation__user__OrgRelationship__organization__isOrgPaying = True)
#       )

#     if payingCoachedGroups.count() > 0:
#       # and some groups pay on their behalf... then user is exempt
#       indivPay = False



#     if (totalExperts.count() == 0 and totalCoachedGroups.count() == 0):
#       # the the user has no one on ones or group coaches, then user does not need to pay
#       indivPay = False 


#   # action items on braintree's end
#   if hasActiveSub == False and indivPay == True and isTrial == False and u.is_staff == False:
#     # if these conditions are met, this user is redirected to the pay wall
#     return True
#     # showPayWall_list.append(u.id)

#   else:
#     # hidePayWall_list.append(u.id)
#     return False


# def checkAllAccountStatus():
#   """
#   looks over all users and determines if they need to be redirected to paywall
#   - switches on paywall redirection if they do 
#   - cancels user's active or pending subscriptions if their account is paid for by a coach
#   - 
#   """

#   print '... checkAllAccountStatus'

#   # grab all users model

#   User = get_user_model()

#   # r = map(lambda u: (u.id ,validatePayWall(u)) , Users)
#   r = [(u.id, validatePayWall(u)) for u in User.objects.all()]
  
#   showPayWall_list = [i[0] for i in filter(lambda x: x[1]==True, r)]
#   hidePayWall_list = [i[0] for i in filter(lambda x: x[1]==False, r)]


#   # edit server user lists
#   # print 'showPayWall_list', showPayWall_list
#   # print 'hidePayWall_list', hidePayWall_list

#   User.objects.filter(id__in = showPayWall_list).update(showPayWall = True)
#   User.objects.filter(id__in = hidePayWall_list).update(showPayWall = False)

#   return r

# from django.db.models import Count
# from django.db import transaction


# def recordOrganizationAuditTrail():
#   """
#   record the users and their role in the organization every day
#   - coaches with no trainees are not billed and not included in the audit trail
#   """
#   print '... recording org audit trail'
  
#   today = timezone.now().date()

#   for o in Organization.objects.all():
#     # print o
#     # expertUsers = o.OrgRelationship.filter(expertUser__TraineeExpertRelation_expert__gt = 0).values('expertUser')
    
#     expertUsers = o.OrgRelationship.annotate(
#       num_trainee=Count("expertUser__TraineeExpertRelation_expert")
#       ).filter(
#         # exclude experts with no trainees
#         num_trainee__gt = 0
#       ).values(
#         'expertUser', 
#         # 'num_trainee'
#       ).distinct()
    
    
#     # extract one-on-one relationships of these experts
#     traineeUsers = TraineeExpertRelation.objects.filter(expertUser__in = expertUsers).values('traineeUser').distinct()

#     # extract group member relationships of these experts
#     groups = Group.objects.filter(
#       GroupMemberRelation__user__in = expertUsers, 
#       GroupMemberRelation__isGroupCoach = True)

#     groupMembers = GroupMemberRelation.objects.filter(group__in = groups).values('user').distinct()

#     # print 'groupMembers', groupMembers


#     # assemble user list and roles
#     # start from the largest pool of users, as the smaller list of common users will overwrite their role
#     org_users = {i['user']: ORG_GROUPMEMBER for i in groupMembers }

#     # trainees comes next
#     for i in traineeUsers:
#       org_users[i['traineeUser']] = ORG_TRAINEE

#     # experts are charged as experts even if they are simultaneously charged as trainees
#     for i in expertUsers:
#       org_users[i['expertUser']] = ORG_EXPERT


#     # filter out users in trial, they will not be charged within trial period:
#     User = get_user_model()
#     now = timezone.now()

#     non_trial_users = User.objects.filter(
#       id__in = org_users, 
#       date_joined__lte = now - datetime.timedelta(days = settings.TRIAL_DAYS_COUNT)  
#       ).values('id')
#     # print 'filtered, non_trial_users:', non_trial_users

#     org_users = {i['id']: org_users[i['id']] for i in non_trial_users}

#     # print 'filtered, non trial users:', org_users


#     insertPayload = []
#     for u in org_users:
#       insertPayload.append(OrganizationAuditTrail(recordDate = today, organization = o, user_id = u, role = org_users[u] ))


#     # print o.name ,'expertUsers', expertUsers
#     # print o.name ,'traineeUsers', traineeUsers

#     with transaction.atomic():
#       # delete old audit trail for the day
#       OrganizationAuditTrail.objects.filter(organization = o, recordDate = today).delete()

#       # insert payload in bulk
#       OrganizationAuditTrail.objects.bulk_create(insertPayload)    


# from django.db.models import Count
# from calendar import monthrange

# # >>> from calendar import monthrange
# # Returns weekday of first day of the month and number of days in month, for the specified year and month.
# # >>> monthrange(2011, 2)
# # (1, 28)


# def OrgMonthEndSummary(org_id, dt=None):
#   """
#   given a date, it would look for that month end's report for that organization
#   """

#   org = Organization.objects.get(id = org_id)

#   if dt is None:
#     dt = timezone.now()

#   oa = OrganizationAuditTrail.objects.filter(
#     recordDate__month = dt.month,
#     recordDate__year = dt.year,
#     organization = org
#   ).values('user__email', 'user__name').annotate(
#     Count('user')
#   )

#   _, days_in_month = monthrange(dt.year, dt.month)

#   for i in oa:
#     i['year'] = dt.year
#     i['month'] = dt.month
#     i['prorataMultiplier'] = float(i['user__count']) / days_in_month

#   return oa


















