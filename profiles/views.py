from django.shortcuts import render
from .models import *
from .forms import *

from django.contrib import messages
from django.conf import settings

from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views import generic
from django.shortcuts import render
from django.db.models import Avg, Max, Min, Count
from django.http import HttpResponse, JsonResponse
from django.views.generic.edit import UpdateView, FormView
from django.core.urlresolvers import reverse_lazy


from allauth.account.models import EmailAddress, EmailConfirmation
from rest_framework.authtoken.models import Token
from rest_framework import views
from rest_framework.response import Response
from rest_framework import permissions

from rest_framework.exceptions import PermissionDenied

from rest_auth.views import PasswordChangeView

from django.contrib.auth.views import password_reset_complete







# from django.contrib.auth import password_reset, password_reset_done, password_reset_confirm, password_reset_complete



def logged_in_and_in_group(user):
  r = False
  if user.is_authenticated():
    # current requirement only requires user to be authenticated to be able to use the site
    r = True

    # # group that user needs to be in
    # if user.groups.filter(name='patientGroup').exists():
    #   r = True
  return r

class GroupRequiredMixin(object): 
  # path to be redirected when user is not logged in yet
  login_url = reverse_lazy('profiles:login')
  
  @method_decorator(user_passes_test(logged_in_and_in_group, login_url=login_url))
  def dispatch(self, *args, **kwargs):
    return super(GroupRequiredMixin, self).dispatch(*args, **kwargs)

class CustomPasswordChangeView(PasswordChangeView):
    """
    Calls Django Auth SetPasswordForm save method.
    Accepts the following POST parameters: new_password1, new_password2
    Returns the success/fail message.

    \n updated by @alan
    \n additionally, returns the token of the user so the front end may set the cookie and the user will be redirected to dashboard
    """

    # serializer_class = PasswordChangeSerializer
    # permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # print 'alan changed this CustomPasswordChangeView', request.user, request.user.auth_token.key
        token, _ = Token.objects.get_or_create(user=request.user)

        return Response({
          "success": "New password has been saved.",
          "token": token.key,
          # "redirectURL": settings.SC_APP_URL,

          })

from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.shortcuts import resolve_url
from django.utils.encoding import force_bytes, force_str ,force_text, force_unicode
from django.utils.http import is_safe_url, urlsafe_base64_decode, urlsafe_base64_encode
from django.http import HttpResponseRedirect, QueryDict
from django.template.response import TemplateResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from django.core.exceptions import ValidationError


from django.contrib.auth.forms import (
    AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm,
)
# def custom_password_reset_confirm(request, uidb64=None, token=None,
#                            template_name='registration/password_reset_confirm.html',
#                            token_generator=default_token_generator,
#                            set_password_form=SetPasswordForm,
#                            post_reset_redirect=None,
#                            current_app=None, extra_context=None):

#     if extra_context is None:
#       extra_context = {}

#     # inject token in this place
#     extra_context.update({
#       'token': request.user.auth_token.key,
#       # "redirectURL": settings.SC_APP_URL
#     })


#     return password_reset_confirm(request, uidb64, token,
#                            template_name,
#                            token_generator,
#                            set_password_form,
#                            post_reset_redirect,
#                            current_app, extra_context)


# Doesn't need csrf_protect since no-one can guess the URL
@sensitive_post_parameters()
@never_cache
def custom_password_reset_confirm(request, uidb64=None, token=None,
                           template_name='registration/password_reset_confirm.html',
                           token_generator=default_token_generator,
                           set_password_form=SetPasswordForm,
                           post_reset_redirect=None,
                           current_app=None, extra_context=None):
    """
    View that checks the hash in a password reset link and presents a
    form for entering a new password.
    """
    UserModel = get_user_model()
    assert uidb64 is not None and token is not None  # checked by URLconf
    if post_reset_redirect is None:
        post_reset_redirect = reverse('password_reset_complete')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)
    try:
        # urlsafe_base64_decode() decodes to bytestring on Python 3
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = UserModel._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    loginToken = None
    if user is not None and token_generator.check_token(user, token):
        validlink = True
        title = 'Enter new password'
        loginToken, _ = Token.objects.get_or_create(user=user)

        if request.method == 'POST':
            form = set_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(post_reset_redirect)
        else:
            form = set_password_form(user)
    else:
        validlink = False
        form = None
        title = _('Password reset unsuccessful')
    context = {
        'form': form,
        'title': title,
        'validlink': validlink,
        'loginToken': loginToken
    }
    if extra_context is not None:
        context.update(extra_context)

    if current_app is not None:
        request.current_app = current_app

    return TemplateResponse(request, template_name, context)

def invalid_password_reset(request,
                            template_name='registration/password_reset_invalidUser.html',
                            current_app=None, extra_context=None):
  if extra_context is None:
    extra_context = {}

  # inject token in this place
  extra_context.update({
    # it is not possible to inject tokn here because user may still be anonymous
    # 'token': request.user.auth_token.key,
    "redirectURL": settings.SC_APP_URL
    })

  r = password_reset_complete(
    request = request,
    template_name = template_name,
    extra_context = extra_context
  )
  return r

from django.contrib.sites.shortcuts import get_current_site


def custom_password_reset_complete(request,
                            template_name='registration/password_reset_complete.html',
                            current_app=None, extra_context=None):
  if extra_context is None:
    extra_context = {}

  # inject token in this place
  extra_context.update({
    # it is not possible to inject tokn here because user may still be anonymous
    # 'token': request.user.auth_token.key,
    "redirectURL": settings.SC_APP_URL
    })

  r = password_reset_complete(
    request = request,
    template_name = template_name,
    extra_context = extra_context
  )
  return r

from django.contrib.sites.shortcuts import get_current_site

class CustomPasswordResetForm(PasswordResetForm):

  def clean(self):
    email = self.cleaned_data.get('email')
    usersList = list(self.get_users(email))

    if not usersList:
      # print 'User does not exist'

      raise ValidationError(
          'User does not exist: %(value)s',
          params={'value': email},
      )

    
  def get_users(self, email):
      """Given an email, return matching user(s) who should receive a reset.

      This allows subclasses to more easily customize the default policies
      that prevent inactive users and users with unusable passwords from
      resetting their password.

      """
      active_users = get_user_model()._default_manager.filter(
          email__iexact=email, is_active=True)
      return (u for u in active_users)

  def save(self, domain_override=None,
         subject_template_name='registration/password_reset_subject.txt',
         email_template_name='registration/password_reset_email.html',
         use_https=False, token_generator=default_token_generator,
         from_email=None, request=None, html_email_template_name=None,
         extra_email_context=None):
    """
    Generates a one-use only link for resetting password and sends to the
    user.
    """
    email = self.cleaned_data["email"]

    usersList = list(self.get_users(email))
    for user in usersList:
        if not domain_override:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
        else:
            site_name = domain = domain_override
        context = {
            'email': user.email,
            'domain': domain,
            'site_name': site_name,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': token_generator.make_token(user),
            'protocol': 'https' if use_https else 'http',
        }
        if extra_email_context is not None:
            context.update(extra_email_context)
        self.send_mail(
            subject_template_name, email_template_name, context, from_email,
            user.email, html_email_template_name=html_email_template_name,
        )

@csrf_protect
def custom_password_reset(request,
                   template_name='registration/password_reset_form.html',
                   email_template_name='registration/password_reset_email.html',
                   subject_template_name='registration/password_reset_subject.txt',
                   password_reset_form=CustomPasswordResetForm,
                   token_generator=default_token_generator,
                   post_reset_redirect=None,
                   from_email=None,
                   extra_context=None,
                   html_email_template_name=None,
                   extra_email_context=None):
    if post_reset_redirect is None:
        post_reset_redirect = reverse('password_reset_done')
    else:
        post_reset_redirect = resolve_url(post_reset_redirect)
    if request.method == "POST":
        form = password_reset_form(request.POST)
        if form.is_valid():
            opts = {
                'use_https': request.is_secure(),
                'token_generator': token_generator,
                'from_email': from_email,
                'email_template_name': email_template_name,
                'subject_template_name': subject_template_name,
                'request': request,
                'html_email_template_name': html_email_template_name,
                'extra_email_context': extra_email_context,
            }
            form.save(**opts)
            return HttpResponseRedirect(post_reset_redirect)

        return HttpResponseRedirect('invalidUser/')
    else:
        form = password_reset_form()
    context = {
        'form': form,
        'title': 'Password reset',
    }
    if extra_context is not None:
        context.update(extra_context)

    return TemplateResponse(request, template_name, context)

from rest_framework.authentication import SessionAuthentication 
class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening

class AccountConfirmCompleteView(views.APIView):
# class AccountConfirmCompleteView(generic.View):
  """ some blank view that user gets sent to on registration email, perhaps it should redirect to a more formal page on frontend """

  authentication_classes = (CsrfExemptSessionAuthentication, SessionAuthentication)
  # template_name = 'AccountConfirmCompleteView'
  # exempt from auth, must be open to public
  permission_classes = (permissions.AllowAny,)
  # @throttle to avoid hack

  def post(self, request, key, resetPassword=False ):

    response = {}
    response['userkey'] = key

    response['resetPassword'] = resetPassword

    confirmed = EmailConfirmation.objects.filter(key = key, sent__gte = timezone.now() - datetime.timedelta(days = settings.ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS) )
    
    if not confirmed:
      raise PermissionDenied('invalid or expired key')
    confirmed = confirmed.first()

    user = User.objects.filter(email = confirmed.email_address.user)

    if not user:
      raise PermissionDenied('User does not exists')
    user = user.first()

    token = Token.objects.filter(user = user)
    if not token:
      token, _ = Token.objects.get_or_create(user=user)
    else:
      token = token.first()

    response['token'] = token.key

    # verify email
    confirmed.email_address.verified = True
    confirmed.email_address.set_as_primary(conditional=True)
    confirmed.email_address.save()

    # except:
    #   # invalid key
    #   # response['message'] = 'invalid key'
    #   print 
    #   raise PermissionDenied('invalid or expired key')

    return Response(response)



class DashboardView(GroupRequiredMixin, generic.View):
  """
  ExpertDashboardView is the first view after login the user sees, which contains all the sections available
  This is just for the coach / expert

  """

  def traineesDashboardStats(self, user):
    """generates trainee dashboard stats and info for the dashboard"""

    traineesDashboardStats = []
    trainees = TraineeExpertRelation.objects.filter(expertUser = user).values(
                                                                                      'traineeUser__name', 
                                                                                      'traineeUser__profile_picture_url',
                                                                                       )
    for trainee in trainees:
      traineeStat = {}
      traineeStat['name'] = trainee['traineeUser__name']
      traineeStat['profile_picture_url'] = trainee['traineeUser__profile_picture_url']
      traineeStat['maxHR'] = 100
      traineeStat['someStat'] = 888
      traineeStat['messageFlag'] = 3

      traineesDashboardStats.append(traineeStat)

    return traineesDashboardStats

  def groupDashboardStats(self, user):
    """generates group dashboard stats and info for the dashboard"""
    groupDashboardStats = []
    myGroups = GroupMemberRelation.objects.filter(user = user).values('group','group__name', 'group__picture', 'group__visibility')

    for group in myGroups:
      groupStat = {}
      groupStat['group__name'] = group['group__name']
      groupStat['group__picture'] = group['group__picture']
      groupStat['group__visibility'] = group['group__visibility']
      groupStat['someStat'] = 1234
      groupStat['messageFlag'] = 2


      print group
      users = GroupMemberRelation.objects.filter(group = group['group']).values('user__name', 'user__profile_picture_url')
      print 'users in group:', users
      groupStat['groupMembers'] = users

      # TBD need to extract stats per user by user id

      for i in users:
        print i
        # print 'indiv user:', settings.AUTH_USER_MODEL.objects.filter(user__id = i)
        # print 'indiv user:', self.traineesDashboardStats(i)

      groupDashboardStats.append(groupStat)

    return groupDashboardStats

  def subexpertDashboardStats(self, user):
    """generates subExperts (coaches working for current coach) dashboard stats and info for the dashboard"""
    subexpertDashboardStats = []
    subExperts = SuperExpertExpertRelation.objects.filter(superExpert = user ).values('expert__name', 'expert__profile_picture_url')

    r = {}
    for i in subExperts:
      r = {}
      r['name'] = i['expert__name']
      r['profile_picture_url'] = i['expert__profile_picture_url']
      r['clientNum'] = 2
      r['messageFlag'] = 3

    subexpertDashboardStats.append(r)
    return subexpertDashboardStats

  def get(self, request):

    response = {}
    response['DEBUG'] = settings.DEBUG
    # if request.user.groups.filter(name='debug').exists():
    #   response['debug'] = True

    if request.user.groups.filter(name='expert').exists():
      expertResponse = {}
      expertResponse['header'] = 'EXPERT'

      # Display trainees summaries
      expertResponse['traineesDashboardStats'] = self.traineesDashboardStats(request.user)
      

      # DISPLAY GROUP SUMMARIES
      expertResponse['groupDashboardStats'] = self.groupDashboardStats(request.user)

      # Display coaches/ experts' summaries under current user
      expertResponse['subexpertDashboardStats'] = self.subexpertDashboardStats(request.user)


      response['expert'] = expertResponse
      return render(request,'profiles/expertDashboard.html', 
           response
        )

    else:
      traineeResponse = {}
      traineeResponse['header'] = 'TRAINEE'

      # DISPLAY GROUP SUMMARIES
      traineeResponse['groupDashboardStats'] = self.groupDashboardStats(request.user)

      response['trainee'] = traineeResponse
      return render(request,'profiles/traineeDashboard.html', 
           response
        )



class UpdateSettingsView(FormView):
  form_class = UserForm
  template_name = 'profiles/settings.html'
  success_url = reverse_lazy('profiles:settings')

  def get(self, request, *args, **kwargs):
    form = self.form_class(instance=self.request.user)
    context = self.get_context_data(**kwargs)
    context['form'] = form
    return self.render_to_response(context)

  def form_valid(self, form):
    user = self.request.user
    f = self.form_class(self.request.POST, instance=user)
    f.save()
    messages.add_message(
       self.request, messages.SUCCESS, 'profile updated')
    return super(UpdateSettingsView, self).form_valid(form)

  def form_invalid(self, form):
    response = super(UpdateSettingsView, self).form_invalid(form)
    messages.error(
      self.request, 'Please try again')
    return response

