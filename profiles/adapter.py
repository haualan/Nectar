from __future__ import unicode_literals

import re
import warnings
import json
from pprint import pprint

from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.contrib import messages

try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text

from allauth.utils import (import_attribute, get_user_model,
                     generate_unique_username,
                     resolve_url, get_current_site,
                     build_absolute_uri)
from allauth.account.utils import user_username, user_email, user_field

from allauth.account import app_settings

# Don't bother turning this into a setting, as changing this also
# requires changing the accompanying form error message. So if you
# need to change any of this, simply override clean_username().
USERNAME_REGEX = re.compile(r'^[\w.@+-]+$', re.UNICODE)

from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    def render_mail(self, template_prefix, email, context):
        """
        Renders an e-mail to `email`.  `template_prefix` identifies the
        e-mail that is to be sent, e.g. "account/email/email_confirmation"
        """
        subject = render_to_string('{0}_subject_custom.txt'.format(template_prefix),
                                   context)

        
        # remove superfluous line breaks
        subject = "".join(subject.splitlines()).strip()

        # skip [SC] pefix, @matt doesnt like
        # subject = self.format_email_subject(subject)

        print 'subject: ', subject

        bodies = {}
        for ext in ['html', 'txt']:
            try:
                template_name = '{0}_message_custom.{1}'.format(template_prefix, ext)
                bodies[ext] = render_to_string(template_name,
                                               context).strip()
            except TemplateDoesNotExist:
                if ext == 'txt' and not bodies:
                    # We need at least one body
                    raise
        if 'txt' in bodies:
            msg = EmailMultiAlternatives(subject,
                                         bodies['txt'],
                                         settings.DEFAULT_FROM_EMAIL,
                                         [email])
            if 'html' in bodies:
                msg.attach_alternative(bodies['html'], 'text/html')
        else:
            msg = EmailMessage(subject,
                               bodies['html'],
                               settings.DEFAULT_FROM_EMAIL,
                               [email])
            msg.content_subtype = 'html'  # Main content is now text/html
        return msg

    def send_mail(self, template_prefix, email, context):
        print 'an email is being sent', template_prefix
        msg = self.render_mail(template_prefix, email, context)
        msg.send()

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        current_site = get_current_site(request)
        activate_url = self.get_email_confirmation_url(
            request,
            emailconfirmation)


        ctx = {
            "user": emailconfirmation.email_address.user,
            "activate_url": activate_url,
            "current_site": current_site,
            "key": emailconfirmation.key,
        }


        if request is not None and not request.user.is_anonymous() and len(request.user.name) > 0 :
            ctx["invitedBy"] = request.user.name

        # print 'request.body',request.body, request, request.POST.get('customMessage',None)
        # pprint(request)

        # this is a default custom message for invite
        ctx['customMessage'] = 'Learn to be a creator using technology at our courses for kids and teens.'

        if request is not None:
            # invite Sender can include a message in the email or additional group information
            ctx['customMessage'] = request.POST.get('customMessage',None)

            # if user is invited, they will need to reset password initially
            ctx['resetPassword'] = request.POST.get('resetPassword',False)

        # branch io link injected to email
        ctx['inviteLink'] = make_inviteLink(emailconfirmation.email_address.user, request, ctx )

        ctx['fallback_url'] = '{}?onboarding=true&k={}'.format(settings.SC_APP_URL, ctx['key'])

        if signup:
            email_template = 'account/email/email_confirmation_signup'
        else:
            email_template = 'account/email/email_confirmation'
        get_adapter().send_mail(email_template,
                                emailconfirmation.email_address.email,
                                ctx)






from allauth.account.models import EmailAddress, EmailConfirmation
def manual_send_confirmation_mail(u):
    """
    @matt to onboard users created manually in system where they do not get an email
    - trigger the invite email manually
    - u is expected to be a user instance
    """

    # grab email address set of this user, if it doesn't exist, create one
    ea, _ = u.emailaddress_set.update_or_create(email = u.email, defaults = {'verified': False, 'primary': True})

    # create a new ec to guarantee a new key
    ec = EmailConfirmation.create(ea)
    ec.send( signup=True)

    # caa = CustomAccountAdapter()
    # caa.send_confirmation_mail(
    #     request=None,
    #     emailconfirmation = ec,
    #     signup = True
    #     )


import requests, json
from django.conf import settings

def make_inviteLink(user, request, ctx,  *args, **kwargs):
    invitedBy = None
    if request is not None and not request.user.is_anonymous():
        invitedBy = request.user.name

    print 'invitedBy', invitedBy


    # see here for more examples: https://dev.branch.io/link_configuration/
    data = {
        "branch_key": settings.BRANCHIO_KEY,
        'sdk': 'api',
        'campaign': 'Invite New User',
        'feature': 'Invite',

        'data':  json.dumps({
            'uid': user.id, 
            'invitedEmail': user.email,
            'invitedBy': invitedBy,
            'inviteToken': ctx['key'],
            'invitedName': user.name,


            # type optional : ADVANCED:
            # Set type to 1, to make the URL a one-time use URL. It won't deep link after 1 successful deep link.
            # Set type to 2 to make a Marketing URL. These are URLs that are displayed under the Marketing tab on the dashboard (to also set the marketing title of the link, which shows up in the Marketing tab, set the $marketing_title field in the data dictionary to the value that you would like).
            # default is set to 0, which is the standard Branch links created via our SDK.git

            # 'type': 1,
            # '$one_time_use': True,

            # duration optional : ADVANCED: In seconds. Only set this key if you want to override the match duration for deep link matching. This is the time that Branch allows a click to remain outstanding and be eligible to be matched with a new app session. This is default set to 7200 (2 hours)

            # if ios is not present we fall back to this http url
            '$fallback_url': '{}?onboarding=true&k={}'.format(settings.SC_APP_URL, ctx['key']),

            # https://github.com/BranchMetrics/android-branch-deep-linking/blob/master/README.md#leverage-android-app-links-for-deep-linking
            # do not use $fallback_url, because it overrides all devices not specified, use $desktop_url instead
            '$desktop_url': '{}?onboarding=true&k={}'.format(settings.SC_APP_URL, ctx['key']),


            '$deeplink_path': '?k={}'.format(ctx['key']),

            }),



    }




    headers = {'Content-Type': 'application/json'}

    # print data

    try:  
        r = requests.post('https://api.branch.io/v1/url', data = json.dumps(data), verify=True, headers = headers )
        l = r.json()['url']
    except:
        print('make invite fail')
        print('Headers',r.headers)
        print('URL', r.url)
        print('response', r.text)


    return l


def get_adapter():
    return import_attribute(app_settings.ADAPTER)()