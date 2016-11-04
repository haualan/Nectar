""" Django-admin autoregister -- automatic model registration

## sample admin.py ##

from yourproject.autoregister import autoregister

# register all models defined on each app
autoregister('app1', 'app2', 'app3', ...)

"""

from django.apps import apps
from django.contrib import admin
from authtools.admin import UserAdmin
from django.contrib.admin.sites import AlreadyRegistered
from import_export.admin import ImportExportModelAdmin
from profiles.models import User


@admin.register(User)
class User(UserAdmin):
    # add custom profile related attributes here
    UserAdmin.fieldsets += (
        ('Profile', {
            'fields': ('name', 'username', 'profile_picture_url', 'birth_date', 'gender', 'height_in_meters', 'isSearchable', 'isCoach'),
        }),
    )

def autoregister(app):
  app = apps.get_app_config(app)
  for model in app.get_models():
    # print model
    try:
      # print list(map(lambda x: x.name ,model._meta.fields))[1:]
      class ModAdmin(ImportExportModelAdmin):
        list_display = list(map(lambda x: x.name ,model._meta.fields))[1:]
      admin.site.register(model, ModAdmin)
    except AlreadyRegistered:
      pass

autoregister('profiles')
# autoregister('spirit_topic_private')
# autoregister('spirit_topic')
# autoregister('core')

# autoregister('activities')
# autoregister('sccalendar')
# autoregister('streamView')


