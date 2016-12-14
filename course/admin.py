from django.contrib import admin
from django.contrib.postgres.fields import JSONField

# Register your models here.
from course.models import Challenge

from jsoneditor.forms import JSONEditor


@admin.register(Challenge)
class Challenge(admin.ModelAdmin):
    # add custom profile related attributes here
    formfield_overrides = {
        JSONField:{ 'widget':JSONEditor },
    }


from profiles.admin import autoregister
autoregister('course')
