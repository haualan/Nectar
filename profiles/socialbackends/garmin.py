"""
Garmin OAuth1 backend
"""

from social.backends.oauth import BaseOAuth1, BaseOAuth2
from pprint import pprint

class GarminOAuth(BaseOAuth1):
    """Garmin OAuth 1.0 authentication backend"""
    name = 'garmin'
    # ID_KEY = 'oauth_token'

    testmode = True
    testurl = ''
    if testmode:
      testurl = 'test'

    AUTHORIZATION_URL = 'http://connect{}.garmin.com/oauthConfirm'.format(testurl)
    REQUEST_TOKEN_URL = 'http://connectapi{}.garmin.com/oauth-service-1.0/oauth/request_token'.format(testurl)
    REQUEST_TOKEN_METHOD = 'POST'
    ACCESS_TOKEN_URL = 'http://connectapi{}.garmin.com/oauth-service-1.0/oauth/access_token'.format(testurl)
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_URI_PARAMETER_NAME = 'oauth_callback'
    EXTRA_DATA = [
    ]


    def get_user_id(self, details, response):
      print 'get_user_id garmin response', response
      return response.get('access_token').get('oauth_token')


    def get_user_details(self, response):
      """Return user details from garmin account, which has very little to no detail"""
      print 'ID_KEY', self.ID_KEY
      print 'get_user_details garmin'
      pprint(response)


      fullname, first_name, last_name = self.get_user_names(
          response.get('display_name')
      )

      return {'username': str(response.get('oauth_token')),
              'garmin_uid': response.get('oauth_token'),
              'email': None,
              'fullname': None,
              'first_name': None,
              'last_name': None}

    # def user_data(self, access_token, *args, **kwargs):
    #     """Loads user data from service"""
    #     return self.get_json('https://api.dropbox.com/1/account/info',
    #                          auth=self.oauth_auth(access_token))



# class GarminOAuth2(BaseOAuth2):
#     name = 'garmin'

# garmin test urls
# 1. http://connecttest.garmin.com
# 2. http://connecttest.garmin.com/oauthConfirm
# 3. http://connectapitest.garmin.com/oauth-service-1.0/oauth/access_token
# 4. http://connectapitest.garmin.com/oauth-service-1.0/oauth/request_token

# garmin production urls
# 1. http://connect.garmin.com
# 2. http://connect.garmin.com/oauthConfirm
# 3. http://connectapi.garmin.com/oauth-service-1.0/oauth/access_token
# 4. http://connectapi.garmin.com/oauth-service-1.0/oauth/request_token



    # AUTHORIZATION_URL = 'https://www.strava.com/oauth/authorize'
    # ACCESS_TOKEN_URL = 'https://www.strava.com/oauth/token'
    # ACCESS_TOKEN_METHOD = 'POST'
    # # Strava doesn't check for parameters in redirect_uri and directly appends
    # # the auth parameters to it, ending with an URL like:
    # # http://example.com/complete/strava?redirect_state=xxx?code=xxx&state=xxx
    # # Check issue #259 for details.
    # REDIRECT_STATE = False
    # REVOKE_TOKEN_URL = 'https://www.strava.com/oauth/deauthorize'

    # def get_user_id(self, details, response):
    #     return response['athlete']['id']

    # def get_user_details(self, response):
    #     """Return user details from Strava account"""
    #     # because there is no usernames on strava
    #     username = response['athlete']['id']
    #     email = response['athlete'].get('email', '')
    #     fullname, first_name, last_name = self.get_user_names(
    #         first_name=response['athlete'].get('firstname', ''),
    #         last_name=response['athlete'].get('lastname', ''),
    #     )
    #     return {'username': str(username),
    #             'fullname': fullname,
    #             'first_name': first_name,
    #             'last_name': last_name,
    #             'email': email}

    # def user_data(self, access_token, *args, **kwargs):
    #     """Loads user data from service"""
    #     return self.get_json('https://www.strava.com/api/v3/athlete',
    #                          params={'access_token': access_token})

    # def revoke_token_params(self, token, uid):
    #     params = super(StravaOAuth, self).revoke_token_params(token, uid)
    #     params['access_token'] = token
    #     return params