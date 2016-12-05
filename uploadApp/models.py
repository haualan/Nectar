from __future__ import unicode_literals

from django.db import models


language_choices = (
    ('PYTHON', 'Python'),
    ('MINECRAFT', 'Minecraft'),
    ('3DPRINTING', '3DPrinting'),
    ('APPINVENTOR', 'AppInventor'),
    ('SCRATCH', 'Scratch'),
    ('JAVA', 'Java'),
    ('JS', 'JavaScript'),
)


DEFAULT_PROFILE_PICTURE_URL = 'http://placehold.it/350x350'
  
# Create your models here.
class Project(models.Model):
    # who does this project belong to
    user = models.ForeignKey('profiles.User')
    name = models.CharField(max_length=255, blank=False)
    description = models.TextField(blank=True)

    updated = models.DateTimeField(auto_now=True)

    # icon for the app
    avatar_url = models.URLField('avatar_url',blank=True, default=DEFAULT_PROFILE_PICTURE_URL)

    language = models.CharField( max_length=20, default='PYTHON', choices = language_choices)

    # if true, then it is shown to the world
    isPublic = models.BooleanField(default = False)

# class ProjectScreenshot(models.Model):
#     # screenshots that belong to a project
#     project = models.ForeignKey('Project')
#     userFile = models.ForeignKey('profiles.UserFile')

#     class Meta:
#         unique_together = ('project','userFile',)

# class ProjectPackageFile(models.Model):
#     # multiple files that can be saved along with the project
#     project = models.ForeignKey('Project')
#     userFile = models.ForeignKey('profiles.UserFile')

#     class Meta:
#         unique_together = ('project',)

# class ProjectIconFile(models.Model):
#     # multiple files that can be saved along with the project
#     project = models.ForeignKey('Project')
#     userFile = models.ForeignKey('profiles.UserFile')

#     class Meta:
#         unique_together = ('project',)


purpose_choices = (
    ('screenshot', 'screenshot'),
    ('icon', 'icon'),
    # instructor is a role set by system only
    ('package', 'package'),
    ('source', 'source'),

)


class ProjectSourceFile(models.Model):
    # multiple files that can be saved along with the project
    project = models.ForeignKey('Project')
    userFile = models.ForeignKey('profiles.UserFile')
    purpose = models.CharField(max_length=1, default='G', choices = purpose_choices)

    class Meta:
        unique_together = ('project','userFile',)






