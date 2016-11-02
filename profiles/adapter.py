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


class CustomAccountAdapter(object):

    def stash_verified_email(self, request, email):
        request.session['account_verified_email'] = email

    def unstash_verified_email(self, request):
        ret = request.session.get('account_verified_email')
        request.session['account_verified_email'] = None
        return ret

    def is_email_verified(self, request, email):
        """
        Checks whether or not the email address is already verified
        beyond allauth scope, for example, by having accepted an
        invitation before signing up.
        """
        ret = False
        verified_email = request.session.get('account_verified_email')
        if verified_email:
            ret = verified_email.lower() == email.lower()
        return ret

    def format_email_subject(self, subject):
        prefix = app_settings.EMAIL_SUBJECT_PREFIX
        if prefix is None:
            site = get_current_site()
            prefix = "[{name}] ".format(name=site.name)
        return prefix + force_text(subject)

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

    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after logging in.  Note
        that URLs passed explicitly (e.g. by passing along a `next`
        GET parameter) take precedence over the value returned here.
        """
        # print 'get_login_redirect_url called', getattr(settings, "LOGIN_REDIRECT_URLNAME", None)

        assert request.user.is_authenticated()
        url = getattr(settings, "LOGIN_REDIRECT_URLNAME", None)
        if url:
            warnings.warn("LOGIN_REDIRECT_URLNAME is deprecated, simply"
                          " use LOGIN_REDIRECT_URL with a URL name",
                          DeprecationWarning)
        else:
            url = settings.LOGIN_REDIRECT_URL
        return resolve_url(url)

    def get_logout_redirect_url(self, request):
        """
        Returns the URL to redirect to after the user logs out. Note that
        this method is also invoked if you attempt to log out while no users
        is logged in. Therefore, request.user is not guaranteed to be an
        authenticated user.
        """
        return resolve_url(app_settings.LOGOUT_REDIRECT_URL)

    def get_email_confirmation_redirect_url(self, request):
        """
        The URL to return to after successful e-mail confirmation.
        """
        if request.user.is_authenticated():
            if app_settings.EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL:
                return  \
                    app_settings.EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL
            else:
                return self.get_login_redirect_url(request)
        else:
            return app_settings.EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL

    def is_open_for_signup(self, request):
        """
        Checks whether or not the site is open for signups.
        Next to simply returning True/False you can also intervene the
        regular flow by raising an ImmediateHttpResponse
        """
        return True

    def new_user(self, request):
        """
        Instantiates a new User instance.
        """
        user = get_user_model()()
        return user

    def populate_username(self, request, user):
        """
        Fills in a valid username, if required and missing.  If the
        username is already present it is assumed to be valid
        (unique).
        """

        first_name = user_field(user, 'first_name')
        last_name = user_field(user, 'last_name')
        email = user_email(user)
        username = user_username(user)
        if app_settings.USER_MODEL_USERNAME_FIELD:
            user_username(user,
                          username
                          or self.generate_unique_username([first_name,
                                                            last_name,
                                                            email,
                                                            'user']))

    def generate_unique_username(self, txts, regex=None):
        return generate_unique_username(txts, regex)

    def save_user(self, request, user, form, commit=True):
        """
        Saves a new `User` instance using information provided in the
        signup form.
        """
        # from allauth.account.utils import user_username, user_email, user_field

        data = form.cleaned_data
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        username = data.get('username')
        user_email(user, email)
        user_username(user, username)
        if first_name:
            user_field(user, 'first_name', first_name)
        if last_name:
            user_field(user, 'last_name', last_name)
        if 'password1' in data:
            user.set_password(data["password1"])
        else:
            user.set_unusable_password()
        self.populate_username(request, user)
        if commit:
            # Ability not to commit makes it easier to derive from
            # this adapter by adding
            user.save()
        return user

    def clean_username(self, username):
        """
        Validates the username. You can hook into this if you want to
        (dynamically) restrict what usernames can be chosen.
        """
        if not USERNAME_REGEX.match(username):
            raise forms.ValidationError(_("Usernames can only contain "
                                          "letters, digits and @/./+/-/_."))

        # TODO: Add regexp support to USERNAME_BLACKLIST
        username_blacklist_lower = [ub.lower()
                                    for ub in app_settings.USERNAME_BLACKLIST]
        if username.lower() in username_blacklist_lower:
            raise forms.ValidationError(_("Username can not be used. "
                                          "Please use other username."))
        username_field = app_settings.USER_MODEL_USERNAME_FIELD
        assert username_field
        user_model = get_user_model()
        try:
            query = {username_field + '__iexact': username}
            user_model.objects.get(**query)
        except user_model.DoesNotExist:
            return username
        raise forms.ValidationError(_("This username is already taken. Please "
                                      "choose another."))

    def clean_email(self, email):
        """
        Validates an email value. You can hook into this if you want to
        (dynamically) restrict what email addresses can be chosen.
        """
        return email

    def clean_password(self, password):
        """
        Validates a password. You can hook into this if you want to
        restric the allowed password choices.
        """
        min_length = app_settings.PASSWORD_MIN_LENGTH
        if len(password) < min_length:
            raise forms.ValidationError(_("Password must be a minimum of {0} "
                                          "characters.").format(min_length))
        return password

    def add_message(self, request, level, message_template,
                    message_context=None, extra_tags=''):
        """
        Wrapper of `django.contrib.messages.add_message`, that reads
        the message text from a template.
        """
        if 'django.contrib.messages' in settings.INSTALLED_APPS:
            try:
                if message_context is None:
                    message_context = {}
                message = render_to_string(message_template,
                                           message_context).strip()
                if message:
                    messages.add_message(request, level, message,
                                         extra_tags=extra_tags)
            except TemplateDoesNotExist:
                pass

    def ajax_response(self, request, response, redirect_to=None, form=None):
        data = {}
        status = response.status_code

        if redirect_to:
            status = 200
            data['location'] = redirect_to
        if form:
            if form.is_valid():
                status = 200
            else:
                status = 400
                data['form_errors'] = form._errors
            if hasattr(response, 'render'):
                response.render()
            data['html'] = response.content.decode('utf8')
        return HttpResponse(json.dumps(data),
                            status=status,
                            content_type='application/json')

    def login(self, request, user):
        from django.contrib.auth import login
        # HACK: This is not nice. The proper Django way is to use an
        # authentication backend
        if not hasattr(user, 'backend'):
            user.backend \
                = "allauth.account.auth_backends.AuthenticationBackend"
        login(request, user)

    def confirm_email(self, request, email_address):
        """
        Marks the email address as confirmed on the db
        """
        print 'confirming email....'
        email_address.verified = True
        email_address.set_as_primary(conditional=True)
        email_address.save()

    def set_password(self, user, password):
        user.set_password(password)
        user.save()

    def get_user_search_fields(self):
        user = get_user_model()()
        return filter(lambda a: a and hasattr(user, a),
                      [app_settings.USER_MODEL_USERNAME_FIELD,
                       'first_name', 'last_name', 'email'])

    def is_safe_url(self, url):
        from django.utils.http import is_safe_url
        return is_safe_url(url)

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Constructs the email confirmation (activation) url.
        Note that if you have architected your system such that email
        confirmations are sent outside of the request context `request`
        can be `None` here.
        """
        url = reverse(
            "account_confirm_email",
            args=[emailconfirmation.key])
        ret = build_absolute_uri(
            request,
            url,
            protocol=app_settings.DEFAULT_HTTP_PROTOCOL)
        return ret

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


        if request is not None and not request.user.is_anonymous():
            ctx["invitedBy"] = request.user.name

        # print 'request.body',request.body, request, request.POST.get('customMessage',None)
        # pprint(request)

        # this is a default custom message for invite
        ctx['customMessage'] = 'Sixcycle is the training and communications platform for athletes, coaches, and communities.'

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

            # @matt make this a one-time-use url do we do not walk into mutliple login / disappearing login issues
            # 'type': 1,
            # '$one_time_use': True,

            # duration optional : ADVANCED: In seconds. Only set this key if you want to override the match duration for deep link matching. This is the time that Branch allows a click to remain outstanding and be eligible to be matched with a new app session. This is default set to 7200 (2 hours)


            # '$fallback_url': '{}?onboarding=true&k={}'.format(settings.SC_APP_URL, ctx['key']),

            
            # http://apiclient.miroapps.com/#onboarding
            # if ios is not present we fall back to this http url
            # https://github.com/BranchMetrics/android-branch-deep-linking/blob/master/README.md#leverage-android-app-links-for-deep-linking
            # do not use $fallback_url, because it overrides all devices not specified, use $desktop_url instead
            '$desktop_url': '{}?onboarding=true&k={}'.format(settings.SC_APP_URL, ctx['key']),


            # @alan: as of May 03 2016, this should no longer be sent, only deeplink_path should be sent
            # @alan: as of apr 28, ios_url is being parsed by onboarding live ios app
            # ios url is the fallback url for ios devices ??? but somehow supercedes when sixcyle:// is not responded with
            # '$ios_url': '{}?onboarding=true&k={}'.format('sixcycle://', ctx['key']),

            # @kristo: 06282016, place an itunes link as a fallback
            '$ios_url': 'https://itunes.apple.com/us/app/sixcycle/id800943946?mt=8',



            # '$ios_url': '?k={}'.format(ctx['key']),
            '$deeplink_path': '?k={}'.format(ctx['key']),

            }),



    }




    headers = {'Content-Type': 'application/json'}

    # print data

    try:  
        r = requests.post('https://api.branch.io/v1/url', data = json.dumps(data), verify=True, headers = headers )
        l = r.json()['url']
    except:
        print('Headers',r.headers)
        print('URL', r.url)
        print('response', r.text)
        l = 'http://stg.sixcycle.com/?BranchIOFail=True'

    return l


def get_adapter():
    return import_attribute(app_settings.ADAPTER)()