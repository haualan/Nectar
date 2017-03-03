from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# import spirit.urls

from profiles.views import AccountConfirmCompleteView, CustomPasswordChangeView
# from activities.apiviews import LifeTimeCPView ,StravaSubView, GarminSubView, MobileSubView, RunningZoneView ,ChartingView, ActivitySummaryView, ActivityTimeSeriesView, ActivityMeanMaxView, UtilsView, FBShareView, PerfProUploadView, FBShareUnitsStressView, TPImportView
# from streamView.apiviews import UserNotificationView, CatchMailView
# from sccalendar.apiviews import SetRosterView
from profiles.apiviews import *
# MeView, InviteView, EmailConfirmView, UserCreateView, UserValidateView, SendConfirmationView, UserPublicView, StudentResetPWView, StudentDeactivateView, PaymentChargeUserView, SchoolUpdateOrCreateView, StripeWebhookView, PaymentManualChargeView, PaymentManualRefundView
# , DisconnectSocialView, GeneratePaymentTokenView, CheckoutView, GetPaymentCustView, PaymentListenerView, PaymentBatchProcess, GetOrgMonthEndSummaryView, CancelSubscriptionView
from feed.apiviews import FeedView

from marketing.apiviews import MarketingCustomView

from course.apiviews import CodeNinjaCacheUpdateView


from rest_framework import routers

from profiles.apiviews import clsmembers as profiles_clsmembers
from course.apiviews import clsmembers as course_clsmembers
from feed.apiviews import clsmembers as feed_clsmembers
from uploadApp.apiviews import clsmembers as uploadapp_clsmembers
from action.apiviews import clsmembers as action_clsmembers
from marketing.apiviews import clsmembers as marketing_clsmembers


router = routers.DefaultRouter()
# router = SC_Router()
# print 'profiles_clsmembers:', profiles_clsmembers
clsmembers = profiles_clsmembers
clsmembers += course_clsmembers
clsmembers += feed_clsmembers
clsmembers += uploadapp_clsmembers
clsmembers += action_clsmembers
clsmembers += marketing_clsmembers

for apiview in clsmembers:
  print 'registering:', apiview[1].api_name, apiview[1], apiview[1].api_name
  router.register(prefix = apiview[1].api_name, viewset = apiview[1], base_name = apiview[1].api_name)
  # router.register(prefix = apiview[1].api_name, viewset = apiview[1])



urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('profiles.urls', namespace = "profiles")),
    # url(r'^', include('activities.urls', namespace = "activities")),
    # url(r'^', include('sccalendar.urls', namespace = "sccalendar")),
    # url(r'^', include('streamView.urls', namespace = "streamView")),

    url(r'^accounts/', include('authtools.urls')),
    url('', include('social.apps.django_app.urls', namespace='social')),

    # forum stuff
    # url(r'^', include(spirit.urls)),

    # specific for charting and timeseries related queries
    # url(r'^api/v1/charting/$', ChartingView.as_view(), name = 'charting-list'),
    # url(r'^api/v1/activitysummary/$', ActivitySummaryView.as_view() , name = 'activitysummary-list'),
    # url(r'^api/v1/activitytimeseries/$', ActivityTimeSeriesView.as_view() , name = 'activitytimeseries-list'),
    # url(r'^api/v1/activitymeanmax/$', ActivityMeanMaxView.as_view() , name = 'activitymeanmax-list'),
    # url(r'^api/v1/lifetimecp/$', LifeTimeCPView.as_view() , name = 'lifetimecp-list'),


    # url(r'^api/v1/usernotification/$', UserNotificationView.as_view() , name = 'usernotification-list'),
    
    url(r'^api/v1/userpublic/$', UserPublicView.as_view() , name = 'userpublic-list'),
    
    
    url(r'^api/v1/sendconfirmation/$', SendConfirmationView.as_view() , name = 'sendconfirmation-list'),
    url(r'^api/v1/uservalidate/$', UserValidateView.as_view() , name = 'uservalidate-list'),
    url(r'^api/v1/usercreate/$', UserCreateView.as_view() , name = 'usercreate-list'),
    url(r'^api/v1/studentresetpw/$', StudentResetPWView.as_view() , name = 'studentresetpw-list'),
    url(r'^api/v1/studentdeactivate/$', StudentDeactivateView.as_view() , name = 'studentdeactivate-list'),

    
    url(r'^api/v1/schoolupdateorcreate/$', SchoolUpdateOrCreateView.as_view() , name = 'schoolupdateorcreate-list'),


    


    url(r'^api/v1/invite/$', InviteView.as_view() , name = 'invite-list'),


    
    url(r'^api/v1/codeninjacacheupdate/$', CodeNinjaCacheUpdateView.as_view() , name = 'codeninjacacheupdate-list'),
    
    url(r'^api/v1/marketingcustom/$', MarketingCustomView.as_view() , name = 'marketingcustom-list'),

    # payment views
    url(r'^api/v1/paymentchargeuser/$', PaymentChargeUserView.as_view() , name = 'paymentchargeuser-list'),
    url(r'^api/v1/stripewebhook/$', StripeWebhookView.as_view() , name = 'stripewebhook-list'),

    
    url(r'^api/v1/paymentmanualcharge/$', PaymentManualChargeView.as_view() , name = 'paymentmanualcharge-list'),
    url(r'^api/v1/paymentmanualrefund/$', PaymentManualRefundView.as_view() , name = 'paymentmanualrefund-list'),

    url(r'^api/v1/couponvalidation/$', CouponValidationView.as_view() , name = 'couponvalidation-list'),

    
    
    


]

# rest framework URLs
urlpatterns += [
    # put custom views here to bypass default behavior of rest-auth
    url(r'^rest-auth/registration/account-confirm-email/(?P<key>\w+)/$', AccountConfirmCompleteView.as_view(),
    name='account_confirm_email'),

    url(r'^rest-auth/password/change/$', CustomPasswordChangeView.as_view(),
        name='rest_password_change'),

    url(r'^rest-auth/', include('rest_auth.urls')),
    url(r'^rest-auth/registration/', include('rest_auth.registration.urls')),
    url(r'^auth/', include('rest_framework_social_oauth2.urls')),

    url(r'^api/v1/', include(router.urls)),
    url(r'^api/v1/api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

