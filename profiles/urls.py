from django.conf.urls import url, include
from profiles import views
from profiles import apiviews
from django.contrib.auth.views import login
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings


login_forbidden =  user_passes_test(lambda u: u.is_anonymous(), '/')

urlpatterns = [
    # url(r'^login$', login_forbidden(login),{'template_name': 'profiles/login.html' }, name="login"),
    # url(r'^$', views.DashboardView.as_view(), name='dashboard'),
    # url(r'^traineedashboard$', views.TraineeDashboardView.as_view(), name='traineedashboard'),
    # url(r'^settings$', views.UpdateSettingsView.as_view(), name='settings'),
    # url(r'^settings/(?P<pk>[0-9]+)/$', views.UpdateSettingsView.as_view(), name='settings'),
    # url(r'user/(?P<pk>[0-9]+)/$', views.UpdateSettingsView.as_view(), name='user_update'),
#     url(r'^userResponse$', views.UserResponseView.as_view(), name='userResponse'),
    # url(r'^logout$', 'django.contrib.auth.views.logout', {'next_page': '/login'}, name = 'logout'),


    # url(r'^rest-auth/registration/account-confirm-email/(?P<key>\w+)/$', views.AccountConfirmCompleteView.as_view(),
    # name='account_confirm_email'),
    


]

from profiles.views import *
from django.contrib.auth.views import password_reset_done

# taking care of password reset stuff, not required for API access, but as django templates
urlpatterns += [
    url(r'^user/password/reset/$', 
        custom_password_reset, 
        {   
            'post_reset_redirect' : '/user/password/reset/done/',
            'template_name': 'profiles/password_reset_form.html',
            'html_email_template_name': 'profiles/password_reset_email.html',
            'subject_template_name': 'profiles/password_reset_subject.txt',
            'extra_email_context': {
                'fqdn': settings.SC_API_URL,
                },
            
        },
        name="password_reset"),
    url(r'^user/password/reset/done/$',
        password_reset_done,
        {
            'template_name': 'profiles/password_reset_done.html',
        }),
    # (?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$
    url(r'^user/password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$', 
        custom_password_reset_confirm, 
        {
            'post_reset_redirect' : '/user/password/done/',
            'template_name': 'profiles/password_reset_confirm.html',

        },
        name="password_reset_confirm"),
    url(r'^user/password/done/$', 
        custom_password_reset_complete,
        # 'django.contrib.auth.views.password_reset_complete',
        {
            'template_name': 'profiles/password_reset_complete.html',
        }),

    # ...
]