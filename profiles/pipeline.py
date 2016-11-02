from profiles.models import User
from rest_framework.authtoken.models import Token
from django.core.exceptions import *

def get_profile_picture(backend, user, response, details, *args, **kwargs):
    url = None
    profile = User.objects.get_or_create(email = user)[0]

    if len(profile.profile_picture_url) > 0 and User._meta.get_field('profile_picture_url').get_default() != profile.profile_picture_url:
        print 'skip get_profile_picture... user has existing picture'
        return


    print 'get_profile_picture from social..'
    print 'backend.name:', backend.name

    if backend.name == 'facebook':
        profile.profile_picture_url  = 'http://graph.facebook.com/{0}/picture?height=300&width=300'.format(response['id'])
    elif backend.name == "twitter":
        if response['profile_image_url'] != '':
            if not response.get('default_profile_image'):
                avatar_url = response.get('profile_image_url_https')
                if avatar_url:
                    avatar_url = avatar_url.replace('_normal.', '_bigger.')
                    profile.profile_picture_url = avatar_url
    elif backend.name == "google-oauth2":
        if response['image'].get('url') is not None:
            profile.profile_picture_url  = response['image'].get('url')

    
    profile.save()

def peek_kwargs(backend, user, response, details, strategy, *args, **kwargs):
    print 'backend', backend
    print 'user', user
    print 'response', response
    print 'details', details
    k = strategy.session_get('key')
    print "strategy.session_get('key')", k
    # print "strategy.session", strategy.session


    try:
        user = Token.objects.get(key = k).user
    except ObjectDoesNotExist:
        print 'cannot find user with key...'
        user = None

    print 'user lookup', user

    print 'kwargs',kwargs

    return None

def get_user_from_session_key(backend, user, response, details, strategy, *args, **kwargs):
    """
    overwrites the user from the previous session key if passed along with login request.
    - problem is if user is somehow logged into stg.sixcycle.com, then the user is retrieved from there instead, which we do not want


    """
    print 'prev user:', user
    k = strategy.session_get('key')
    try:
        user = Token.objects.get(key = k).user
    except ObjectDoesNotExist:
        print 'cannot find user with key..., set user to none, must discard previous user in session from stg'
        user = None

    
    return {
        'user': user
        }


