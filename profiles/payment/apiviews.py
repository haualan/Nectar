from .utils import *
from rest_framework import viewsets, filters, generics, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from rest_framework.exceptions import APIException, ParseError, PermissionDenied
from profiles.models import OrgRelationship
from .serializers import *

from threading import Thread
def postpone(function):
  def decorator(*args, **kwargs):
    t = Thread(target = function, args=args, kwargs=kwargs)
    t.daemon = True
    t.start()
  return decorator



class PaymentBatchProcess(views.APIView):
    """
    Kicks off batch processing on the server to collect billing data on users
    """

    api_name = 'paymentbatchprocess'
    http_method_names = ['post']
    permission_classes = (AllowAny, )

    @postpone
    def runProcesses(self):
        print 'runProcesses batch '
        
        c = checkAllAccountStatus()
        

        
        r = recordOrganizationAuditTrail()
        

    def post(self, request, format=None, *args, **kwargs):
        # u = request.user
        print 'paymentbatchprocess.... recd'


        signature = None
        try:
            data = request.data
            signature = data['signature']
        except:
            raise PermissionDenied('invalid signature')

        if signature != settings.BATCH_KEY:
            raise PermissionDenied('invalid signature')


        # if signature is parsed and correct, kick off batch processes
        # on a sepearate thred
        self.runProcesses()


        return Response({}, status=200)



class CancelSubscriptionView(views.APIView):
    """
    loops through all user subscriptions and cancels them all
    """

    api_name = 'cancelsubscription'
    http_method_names = ['post']
    permission_classes = (IsAuthenticated, )

    def post(self, request, format=None, *args, **kwargs):
        u = request.user

        print 'cancelsubscription', u 


        token, customer = generate_payment_token(user = u)



        # make sure user has no active or pending subscription of same plan
        subs = map(lambda x: x.subscriptions ,customer.payment_methods)
        print len(subs)

        # flatten subs
        subs = list(itertools.chain(*subs))
        print len(subs), [i.id for i in subs]

        # filter subscrciptions that are active, pending, or pastdue
        subs = filter(lambda x: x.status in [        
            braintree.Subscription.Status.Active,
            # braintree.Subscription.Status.Canceled,
            # braintree.Subscription.Status.Expired,
            braintree.Subscription.Status.PastDue,
            braintree.Subscription.Status.Pending
            ], subs )

        print len(subs), [i.id for i in subs]

        # cancel all extra subs that aren't supposed to be there
        # enforce all users to only have one current sub
        for s in subs:
            print 'canceling sub :', s.id
            try:
                result = braintree.Subscription.cancel(s.id)
            except:
                print 'failed to cancel sub:', s.id


        return Response({'token': token})




class GetPaymentCustView(views.APIView):
    """
    returns braintree token for a user, only the logged in user can see and edit token (strictly). tokens for different users should only be accessed thru shell
    """

    api_name = 'getpaymentcust'
    http_method_names = ['get']
    permission_classes = (IsAuthenticated, )

    def get(self, request, format=None, *args, **kwargs):
        u = request.user

        customer = customer_create_or_update(user = u)

        return Response({'customer_id': customer.id})




class GeneratePaymentTokenView(views.APIView):
    """
    returns a payment token from braintree and additionally looks if user has existing active or pending plans (so front end can control if this needs to be updated)
    """

    api_name = 'generatepaymenttoken'
    http_method_names = ['get']
    permission_classes = (IsAuthenticated, )


    def get(self, request, format=None, *args, **kwargs):
        u = request.user

        print 'generatepaymenttoken', u 


        token, customer = generate_payment_token(user = u)



        # make sure user has no active or pending subscription of same plan
        subs = map(lambda x: x.subscriptions ,customer.payment_methods)
        print len(subs)

        # flatten subs
        subs = list(itertools.chain(*subs))
        print len(subs), [i.id for i in subs]

        # filter subscrciptions that are active, pending, or pastdue
        subs = filter(lambda x: x.status in [        
            braintree.Subscription.Status.Active,
            # braintree.Subscription.Status.Canceled,
            # braintree.Subscription.Status.Expired,
            braintree.Subscription.Status.PastDue,
            braintree.Subscription.Status.Pending
            ], subs )

        print len(subs), [i.id for i in subs]

        current_sub = None
        if len(subs) > 0:
            current_sub = subs[0].id

        # cancel all extra subs that aren't supposed to be there
        # enforce all users to only have one current sub
        for s in subs[1:]:
            print 'found extraneous subscribed plan... canceling :', s.id
            try:
                result = braintree.Subscription.cancel(s.id)
            except:
                print 'failed to cancel plan:', s.id


        return Response({'token': token, 'current_sub': current_sub})

from rest_framework.authentication import TokenAuthentication
class CheckoutView(views.APIView):
    """
    returns a payment token from braintree
    """

    api_name = 'checkout'
    http_method_names = ['post']
    permission_classes = (IsAuthenticated, )
    # authentication_classes = (TokenAuthentication,)


    def post(self, request, format=None, *args, **kwargs):
        u = request.user

        print 'checkout', u , request.data

        nonce = request.data['payment_method_nonce']
        current_sub =request.data['current_sub']

        # result = braintree.Transaction.sale({
        #     "amount": "10.00",
        #     "payment_method_nonce": nonce,
        #     "options": {
        #       "submit_for_settlement": True
        #     }
        # })



        if current_sub is None:
            # if new plan is chosen
            result = braintree.Subscription.create({
                # this is the token for the payment method, not the nonce
                # "payment_method_token": token

                "payment_method_nonce": nonce,
                "plan_id": settings.BRAINTREE_BASIC_PLAN,

                # if not included, will just use default acct in USD
                # "merchant_account_id": "gbp_account"
            })
        else:
            # update the sub with new payment info, otherwise, users cannot
            result = braintree.Subscription.update(current_sub, {
                "payment_method_nonce": nonce,
                "plan_id": settings.BRAINTREE_BASIC_PLAN,
            })


        # result.is_success
        # True
        print nonce, result

        status = ''
        # "authorized"

        

        if result.is_success == False:
            # if payment fails, return a message and do not redirect further

            # for error in result.errors.deep_errors:
            #     print(error.attribute)
            #     print(error.code)
            #     print(error.message)

            #     status += error.message + ' '

            return Response({'msg': result.subscription.status}, status=403)

        
        # if payment is success we assume active sub
        # we assume not show paywall
        u.showPayWall = False
        u.save()
        p = u.Payment.all().first()
        if p:
            p.hasActiveSub = True
            p.save()

        return Response({'msg': result.subscription.status }, status=201)


from rest_framework.authentication import TokenAuthentication
class PaymentListenerView(views.APIView):
    """
    Listens for Braintree webhook events
    https://developers.braintreepayments.com/guides/webhooks/overview
    """

    api_name = 'paymentlistener'
    http_method_names = ['post']
    permission_classes = (AllowAny, )
    # authentication_classes = (TokenAuthentication,)


    def post(self, request, format=None, *args, **kwargs):

        # unpack payload from braintree
        b_notification = request.data

        # print 'webhook_notification', b_notification

        try:
            webhook_notification = braintree.WebhookNotification.parse(
              b_notification['bt_signature'],
              b_notification['bt_payload']
            )
        except:
            raise ParseError("malformed payload")


        # Check what kind of notification this is

        # print 'webhook_notification', webhook_notification

        print webhook_notification.kind
        # => "subscription_went_past_due"

        # checks and operations with no repercussions should do nothing and return success
        if webhook_notification.kind in [
            braintree.WebhookNotification.Kind.Check,
            braintree.WebhookNotification.Kind.SubscriptionTrialEnded,
            ]:
            print 'braintree check successful'
            return Response({}, status=200)

        if webhook_notification.kind in [
            braintree.WebhookNotification.Kind.SubscriptionChargedUnsuccessfully,
            braintree.WebhookNotification.Kind.SubscriptionExpired,
            braintree.WebhookNotification.Kind.SubscriptionCanceled,
            braintree.WebhookNotification.Kind.SubscriptionWentPastDue,
            ]:

            print 'braintree sub canceled or ended, flip user account switch off'



            # check braintree for existing active subs on this user

        if webhook_notification.kind in [
            braintree.WebhookNotification.Kind.SubscriptionChargedSuccessfully,
            braintree.WebhookNotification.Kind.SubscriptionWentActive
            ]:

            print 'braintree sub active, flip user account switch on'


        
        sub = webhook_notification.subscription

        pmt = sub.payment_method_token

        paymentMethod = braintree.PaymentMethod.find(pmt)

        # finally get to the customer ID
        cust_id = paymentMethod.customer_id
        customer = braintree.Customer.find(cust_id)

        # update or create item in Payment and check to see if user has other active subs
        # if not, then mark user as false
        has_active_sub(user = None, customer = customer)

        # try to find user via cust_id in Payments table
        u = None
        try:
            int(cust_id)
            u = Payment.objects.get(cust_id = cust_id).user
        except:
            print 'braintree customer_id:', cust_id, 'not found in sixcycle'
            u = None

        if u:
            pw_status = validatePayWall(u)
            print 'updated user status to:', u.email,pw_status 
            User.objects.filter(id = u.id).update(showPayWall = pw_status)





        print webhook_notification.timestamp
        # => Sun Jan 1 00:00:00 UTC 2012

        # print webhook_notification.subscription.id
        # => "subscription_id"



        return Response({}, status=200)



class GetOrgMonthEndSummaryView(views.APIView):
    """
    returns non-standard billing monthly usage report for an organization
    query params:
    dt = iso date time, report will be for the month-end of the date passed, if not passed, then will generate report for current month
    org_id = organization ID

    \n example: https://localhost:8000/api/v1/getorgmonthendsummary/?org_id=1&dt=2014-03-05T00:00:00
    """

    api_name = 'getorgmonthendsummary'
    http_method_names = ['get']
    permission_classes = (IsAuthenticated, )

    def get(self, request, format=None, *args, **kwargs):
        # logged in user must either supply signature so internal users can look at this report or be an expertUser of this organization 
        

        # print request.query_params
        payload = {
            'org_id': self.request.query_params.get('org_id', None),
            'dt': self.request.query_params.get('dt', None),
            's' : self.request.query_params.get('s', None)
        }

        for i in request.data:
            payload[i] = request.data[i]

        # print 'payload', payload
        if not payload['dt']:
            payload.pop('dt')
        if not payload['s']:
            payload.pop('s')

        serializer = GetOrgMonthEndSummarySerializer(data = payload)

        serializer.is_valid(raise_exception = True)


        org_id = serializer.validated_data.get('org_id')
        dt = serializer.validated_data.get('dt')

        orgRel = OrgRelationship.objects.filter(
            organization_id = org_id, 
            expertUser = request.user)

        print 'org_id, dt', org_id, dt






        # org_id = self.request.query_params.get('org_id', None)
        # dt = self.request.query_params.get('dt', None)

        # if org_id is None:
        #     raise PermissionDenied('org_id must be supplied')

        signature = serializer.validated_data.get('s')
        
        if orgRel.count() == 0 and request.user.is_staff == False :
            raise PermissionDenied('You are not an expert User of this organization')

        return Response(OrgMonthEndSummary(org_id, dt))









