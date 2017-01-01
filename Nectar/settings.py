

"""
Django settings for Nectar project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

from __future__ import unicode_literals




import os, sys, codecs, locale

# set UTF 8 encoding so we can print unicode chars in output, but only if not in iPYTHON interactive shell
# in ipython, the computer sends ascii but the console only catches UTF-8 if this is set...
if not sys.__stdin__.isatty():
    sys.stdout = codecs.getwriter('UTF-8')(sys.stdout)

# from spiritSettings import *
# print INSTALLED_APPS


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# for aws S3 storage
from boto.s3.connection import SubdomainCallingFormat

AWS_QUERYSTRING_AUTH = False







# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'a7wij3z=e%dp1bpsj^lh9_)0d#(y3v)ukpb9zpvxjy*4ksrw9c'
# import django
# django.setup()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


# change to True if pushing to production
remoteHost = False


if remoteHost:
    ALLOWED_HOSTS = [
        '.firstcodeacademy.com', # Allow domain and subdomains
        '.firstcodeacademy.com.', # Also allow FQDN and subdomains
        '52.220.123.222',
    ]


# Application definition
if 'INSTALLED_APPS' not in globals():
    INSTALLED_APPS = []
    
INSTALLED_APPS.extend([
    

    # 'spirit'

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'sslserver',
    'corsheaders',

    # for creating and editing challenges
    'jsoneditor',
    


    'rest_framework',
    'rest_framework.authtoken',
    'rest_auth',

    # # registration does not work unless allauth is in place
    'allauth',
    'allauth.account',
    'rest_auth.registration',

    # # 'spirit',

    # # django-storages to store uploaded files to s3
    'storages',


    'profiles',
    'course',
    'uploadApp',
    'feed',
    'action',

    'marketing',

    'djfrontend',
    'djfrontend.skeleton',
    'import_export',

    # # social auth apps
    'oauth2_provider',

    'social.apps.django_app.default',
    'rest_framework_social_oauth2',

    'authtools',
    # # for the love of debugging
    'debug_toolbar',
    'django_extensions',
])

REST_FRAMEWORK = {
    # 'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAdminUser',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticatedOrReadOnly',),
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'DEFAULT_METADATA_CLASS': 'profiles.utils.MinimalMetadata',
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_PAGINATION_CLASS': 'profiles.pagination.SC_PageNumberPagination',
    # specifying the renderers
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # consider shutting off Basic and Session Auth on production for API
        'rest_framework.authentication.TokenAuthentication',

        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',

        
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
        'rest_framework_social_oauth2.authentication.SocialAuthentication',
    )
}

# django-allauth handles user registration workflow, settings here
# https://github.com/pennersr/django-allauth/blob/master/allauth/account/forms.py
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[FirstCodeAcademy] '
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 30


# controls jsoneditor styling
JSON_EDITOR_JS = 'https://cdnjs.cloudflare.com/ajax/libs/jsoneditor/4.2.1/jsoneditor.js'
JSON_EDITOR_CSS = 'https://cdnjs.cloudflare.com/ajax/libs/jsoneditor/4.2.1/jsoneditor.css'




ACCOUNT_ADAPTER = 'profiles.adapter.CustomAccountAdapter'


# this is the name of the API for external users
 # https://github.com/PhilipGarnero/django-rest-framework-social-oauth2  
PROPRIETARY_BACKEND_NAME = 'FCA'

AUTH_USER_MODEL = 'profiles.User'

if 'MIDDLEWARE_CLASSES' not in globals():
    MIDDLEWARE_CLASSES = []
MIDDLEWARE_CLASSES.extend([
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
])

if 'TEMPLATES' not in globals():
    TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': (
            os.path.join(BASE_DIR, 'templates/account/em'),
        ),
        'OPTIONS': {
            'context_processors': [],
            },
        }
    ]
TEMPLATES[0]['OPTIONS']['context_processors'].extend([
# TEMPLATE_CONTEXT_PROCESSORS =
    'social.apps.django_app.context_processors.backends',
    'social.apps.django_app.context_processors.login_redirect',
    'django.contrib.auth.context_processors.auth',
    # 'django.core.context_processors.debug',
    # 'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'django.template.context_processors.request',
])


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django.log'),
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}

ROOT_URLCONF = 'Nectar.urls'

# Apache / Security Settings
WSGI_APPLICATION = 'Nectar.wsgi.application'
#CORS_ORIGIN_ALLOW_ALL = False

# Session related settings
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
# set SSL redirect to True on Production
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# DEBUG TOOLBAR SETTINGS
# DEBUG_TOOLBAR_PATCH_SETTINGS = False



REST_AUTH_SERIALIZERS = {
    'LOGIN_SERIALIZER': 'profiles.serializers.CustomLoginSerializer',
    # 'TOKEN_SERIALIZER': 'rest_auth.serializers.TokenSerializer',
    'TOKEN_SERIALIZER': 'profiles.serializers.CustomTokenSerializer',
    'USER_DETAILS_SERIALIZER':'rest_auth.serializers.UserDetailsSerializer',
    'PASSWORD_RESET_SERIALIZER': 'profiles.serializers.CustomPasswordResetSerializer',
    'PASSWORD_RESET_CONFIRM_SERIALIZER':'rest_auth.serializers.PasswordResetConfirmSerializer',
    'PASSWORD_CHANGE_SERIALIZER':'rest_auth.serializers.PasswordChangeSerializer',

}

# keeps user logged in after pw reset 
LOGOUT_ON_PASSWORD_CHANGE = False

REST_AUTH_REGISTRATION_SERIALIZERS = {
    # 'REGISTER_SERIALIZER': 'rest_auth.register.serializers.RegisterSerializer',
    'REGISTER_SERIALIZER': 'profiles.registration.CustomRegisterSerialize',
}

# Oauth social login settings:
if 'AUTHENTICATION_BACKENDS' not in globals():
    AUTHENTICATION_BACKENDS = []
AUTHENTICATION_BACKENDS.extend([
    # 'social.backends.open_id.OpenIdAuth',
    'social.backends.facebook.FacebookOAuth2',
    'social.backends.google.GoogleOpenId',
    'social.backends.google.GoogleOAuth2',
    'social.backends.google.GoogleOAuth',
    # 'social.backends.fitbit.FitbitOAuth',
    # 'social.backends.strava.StravaOAuth',
    # 'profiles.socialbackends.garmin.GarminOAuth',
    # 'social.backends.twitter.TwitterOAuth',
    # 'social.backends.yahoo.YahooOpenId',

    'rest_framework_social_oauth2.backends.DjangoOAuth2',
    # 'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
])



SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'public_profile', 'user_friends' ]
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {'locale': 'en_US'}
SOCIAL_AUTH_FACEBOOK_EXTRA_DATA = [  
    # pattern is (source key, destination key)
    ('email', 'email'),
]



# LOGIN_ERROR_URL    = '/login-error/'

SOCIAL_AUTH_FIELDS_STORED_IN_SESSION = ['key',] 


SOCIAL_AUTH_USER_MODEL = 'profiles.User'

# only for mysql backend to enforce field length, some oauth ppl use longer retarded keys
SOCIAL_AUTH_UID_LENGTH = 223

SOCIAL_AUTH_DEFAULT_USERNAME = 'user'

# only needed if email is username
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True

# for security
SOCIAL_AUTH_FORCE_POST_DISCONNECT = True

# These URLs are used on different steps of the auth process, some for successful results and others for error situations.
### see config.py, link depends on the live/stg server


SOCIAL_AUTH_PIPELINE = (
    'profiles.pipeline.peek_kwargs',

    # Get the information we can about the user and return it in a simple
    # format to create the user instance later. On some cases the details are
    # already part of the auth response from the provider, but sometimes this
    # could hit a provider API.
    'social.pipeline.social_auth.social_details',

    # Get the social uid from whichever service we're authing thru. The uid is
    # the unique identifier of the given user in the provider.
    'social.pipeline.social_auth.social_uid',

    # Verifies that the current auth process is valid within the current
    # project, this is were emails and domains whitelists are applied (if
    # defined).
    'social.pipeline.social_auth.auth_allowed',

    # Checks if the current social-account is already associated in the site.
    'social.pipeline.social_auth.social_user',

    # gets user from user token @Alan
    'profiles.pipeline.get_user_from_session_key',

    # Make up a username for this person, appends a random string at the end if
    # there's any collision.
    'social.pipeline.user.get_username',

    # Send a validation email to the user to verify its email address.
    # Disabled by default.
    # 'social.pipeline.mail.mail_validation',

    # Associates the current social details with another user account with
    # a similar email address. Disabled by default.
    'social.pipeline.social_auth.associate_by_email',

    # Create a user account if we haven't found one yet.
    'social.pipeline.user.create_user',

    # Create the record that associated the social account with this user.
    'social.pipeline.social_auth.associate_user',

    # Populate the extra_data field in the social record with the values
    # specified by settings (and the default ones like access_token, etc).
    'social.pipeline.social_auth.load_extra_data',

    # Update the user record with any changed info from the auth service.
    'social.pipeline.user.user_details',

    # grabs pictures if available in social provider
    # uncomment to turn on
    'profiles.pipeline.get_profile_picture',
)



# commands to load numpy fitted models and other similar items in memory to reduce  disk I/O
# will crash mod_wsgi in apache, cannot use
# from sklearn.externals import joblib
# WALKING_MODEL = joblib.load(BASE_DIR + '/activities/statistics/pacemodel/' + 'paceModel.pkl') 

# import pickle
# WALKING_MODEL = pickle.load(open(BASE_DIR + '/activities/statistics/pacemodel/' + 'paceModel.p')) 

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }

# if remoteHost:
#     DATABASES = PROD_DATABASES
# else:

# AWS file storage for raw data:
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
AWS_CALLING_FORMAT = SubdomainCallingFormat
STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'fcadb',
        'USER': 'djangouser',
        'PASSWORD': '1q2w3e4r',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    },
    # 'default': {
    #     'ENGINE': 'django.db.backends.mysql',
    #     'NAME': 'FCADB',
    #     'USER': 'djangomysql',
    #     'PASSWORD': 'djangomysql',
    #     'HOST': '127.0.0.1',
    #     'PORT': '3306',
    # }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/
STATIC_URL = '/static/'




# used to store images of profiles
MEDIA_ROOT= BASE_DIR +'/media/'
MEDIA_URL='/'




from config import *
