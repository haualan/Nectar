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
from profiles.apiviews import MeView, InviteView, EmailConfirmView
# , DisconnectSocialView, GeneratePaymentTokenView, CheckoutView, GetPaymentCustView, PaymentListenerView, PaymentBatchProcess, GetOrgMonthEndSummaryView, CancelSubscriptionView
from feed.apiviews import FeedView


from rest_framework import routers
# from .routers import SC_Router
from profiles.apiviews import clsmembers as profiles_clsmembers
from course.apiviews import clsmembers as course_clsmembers
from feed.apiviews import clsmembers as feed_clsmembers
# from activities.apiviews import clsmembers as activities_clsmembers

router = routers.DefaultRouter()
# router = SC_Router()
# print 'profiles_clsmembers:', profiles_clsmembers
clsmembers = profiles_clsmembers
clsmembers += course_clsmembers
clsmembers += feed_clsmembers
# clsmembers += sccalendar_clsmembers

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
    url(r'^api/v1/invite/$', InviteView.as_view() , name = 'invite-list'),
    url(r'^api/v1/emailconfirm/$', EmailConfirmView.as_view() , name = 'emailconfirm-list'),
    # url(r'^api/v1/userschoolrelationupdateorcreate/$', UserSchoolRelationUpdateOrCreate.as_view(), name = 'userschoolrelationupdateorcreate-list'),

    # url(r'^api/v1/runningzone/$', RunningZoneView.as_view() , name = 'runningzone-list'),

    # url(r'^api/v1/disconnectsocial/$', DisconnectSocialView.as_view() , name = 'disconnectsocial-list'),

    # # StravaSubView is a special endpoint for strava webhooks users
    # url(r'^api/v1/strava/sub/$', StravaSubView.as_view() , name = 'stravasub-list'),

    # # garmin's endpoint for push subscription
    # url(r'^api/v1/garmin/sub/$', GarminSubView.as_view() , name = 'garmin-list'),

    # # mobile endpoint to recieve data
    # url(r'^api/v1/mobile/sub/$', MobileSubView.as_view() , name = 'mobilesub-list'),


    # # setroster custom endpoint for rsvp roster
    # url(r'^api/v1/setroster/$', SetRosterView.as_view() , name = 'setroster-list'),


    # # utilsview for general get only items to assist front end
    # url(r'^api/v1/utils/$', UtilsView.as_view() , name = 'utils-list'),

    # # FBShareView for perfpro to post their data to our server
    # url(r'^api/v1/fbshare/$', FBShareView.as_view() , name = 'fbshare-list'),

    # # PerfProUploadView to get data for sharing activities on FB
    # url(r'^api/v1/upload$', PerfProUploadView.as_view() , name = 'upload-list'),
    # url(r'^api/v1/upload/$', PerfProUploadView.as_view() , name = 'upload-list'),

    # # FBShare requires units
    # url(r'^api/v1/fbshareunitsstress/$', FBShareUnitsStressView.as_view() , name = 'fbshareunitsstress-list'),

    # # tp import view
    # url(r'^api/v1/tpimport/$', TPImportView.as_view() , name = 'tpimport-list'),

    # # payment views
    
    # url(r'^api/v1/getpaymentcust/$', GetPaymentCustView.as_view() , name = 'getpaymentcust-list'),
    # url(r'^api/v1/generatepaymenttoken/$', GeneratePaymentTokenView.as_view() , name = 'generatepaymenttoken-list'),
    # url(r'^api/v1/checkout/$', CheckoutView.as_view() , name = 'checkout-list'),
    # url(r'^api/v1/cancelsubscription/$', CancelSubscriptionView.as_view() , name = 'cancelsubscription-list'),



    # url(r'^api/v1/paymentlistener/$', PaymentListenerView.as_view() , name = 'paymentlistener-list'),
    # url(r'^api/v1/paymentbatchprocess/$', PaymentBatchProcess.as_view() , name = 'paymentbatchprocess-list'),
    # url(r'^api/v1/getorgmonthendsummary/$', GetOrgMonthEndSummaryView.as_view() , name = 'getorgmonthendsummary-list'),


    # # catch mail from mailgun
    # url(r'^api/v1/catchmail/$', CatchMailView.as_view() , name = 'catchmail-list'),


    # url(r'^api/v1/me/$', MeView.as_view()),
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

