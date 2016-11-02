"""
WSGI config for SixCycle project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SixCycle.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# from django.core.handlers.wsgi import WSGIHandler
# application = WSGIHandler()


# try t orewrite pw checking?
# from django.contrib.auth.handlers.modwsgi import check_password


from django import db
from django.contrib import auth
from django.utils.encoding import force_bytes


def check_password(environ, username, password):
    """
    Authenticates against Django's auth database
    mod_wsgi docs specify None, True, False as return value depending
    on whether the user exists and authenticates.
    """

    print 'check_password', username, password

    UserModel = auth.get_user_model()
    # db connection state is managed similarly to the wsgi handler
    # as mod_wsgi may call these functions outside of a request/response cycle
    db.reset_queries()

    try:
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            return None
        if not user.is_active:
            return None
        return user.check_password(password)
    finally:
        db.close_old_connections()