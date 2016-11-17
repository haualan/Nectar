from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
from django.conf import settings
from django.dispatch import receiver
from django.forms import ModelForm
from datetime import datetime
from django.db.models import Count

from rest_framework.authtoken.models import Token
from authtools.models import AbstractEmailUser


from datetime import timedelta
import dateutil.parser
import uuid, os

# from activities.statistics.heartratemodel.utils import *
# from activities.statistics.jackdaniels import calc_JD_pace_heartrate


gender_choices = (
      ('M', 'male'),
      ('F', 'female'),
  )

role_choices = (
      ('G', 'guardian'),
      ('S', 'student'),
  )
import pytz
tzName_choices = set((i, i) for i in pytz.all_timezones)

def get_eighteen_yearoldDate():
  return datetime((timezone.now().year - 18), 1, 1)

def get_default_age():
  return datetime((timezone.now().year - 30), 1, 1)

DEFAULT_PROFILE_PICTURE_URL = 'http://placehold.it/350x350'

class User(AbstractEmailUser):
  avatar_url = models.URLField('avatar_url',blank=True, default=DEFAULT_PROFILE_PICTURE_URL)
  birth_date = models.DateField('birth_date', blank=True, default=get_default_age)
  gender = models.CharField('gender', max_length=1, default='M', choices = gender_choices)
  firstname = models.CharField('firstname', max_length=255, blank=True)
  lastname = models.CharField('lastname', max_length=255, blank=True)

  username = models.CharField('username', max_length=255, blank=True)

  # timezone offset relative to UTC
  tzName = models.CharField(max_length=100, default = 'Hongkong',  choices = tzName_choices)
  phoneNumber = models.CharField(max_length=50, blank=True, null=True)
  location = models.CharField(max_length=100, blank=True, null=True)

  lon = models.DecimalField(max_digits=9, decimal_places=6, null=True)
  lat = models.DecimalField(max_digits=9, decimal_places=6, null=True)

  # controls whether front end should trigger onboarding when logged in.
  hasOnboarded = models.BooleanField(default = False)


  isSearchable = models.BooleanField(default = True)

  # controls whether email notifications are sent.
  isEmailNotified = models.BooleanField(default = True)

  # controls whether paywall is active for user
  showPayWall = models.BooleanField(default = False)

  # user roles: can be a parent or coach
  role = models.CharField(max_length=1, default='G', choices = role_choices)



  def save(self, *args, **kwargs):
    # truncate any query params on the url @jon issue with s3 temporary validation links 02/27/2016
    # try:
    #   self.profile_picture_url = self.profile_picture_url.split('?')[0]
    # except:
    #   pass

    super(User, self).save(*args, **kwargs) # Call the "real" save() method.
  

  @property
  def get_mySchools(self):
    """
    returns groups of which this user is a member of
    """
    return School.objects.filter(userschoolrelation__user = self).order_by('name')


  def get_age(self):
    today = datetime.now()
    return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

  def get_full_name(self):
    return self.name




  def __unicode__(self):              
    return self.email

  @property
  def name(self):
    return '{} {}'.format(self.firstname, self.lastname)


class UserForm(ModelForm):
  """
  This is the form fields showing fields a user is allowed to change
  """
  class Meta:
    model = User
    fields = ['email', 'username', 'firstname','lastname', 'avatar_url', 'birth_date', 'gender', 'isSearchable']


class GuardianStudentRelation(models.Model):
  guardian = models.ForeignKey('User')
  student = models.ForeignKey('User', related_name='TraineeExpertRelation_trainee')  

  def __unicode__(self):
    return u'Guardian: %s Student: %s' % (self.guardian, self.student)

  class Meta:
    unique_together = ('guardian', 'student',)

class School(models.Model):
  avatar_url = models.URLField('avatar_url',blank=True, default=DEFAULT_PROFILE_PICTURE_URL)
  name = models.CharField(max_length=255, blank=False)
  lon = models.DecimalField(max_digits=9, decimal_places=6, null=True)
  lat = models.DecimalField(max_digits=9, decimal_places=6, null=True)

  class Meta:
    # schools must be unique
    unique_together = ('name',)



class UserSchoolRelation(models.Model):
  user = models.ForeignKey('User')
  school = models.ForeignKey('School')
  enrollmentDate = models.DateField(blank=True, default=timezone.now)


  class Meta:
    # each user can be associated to multiple schools but only once
    unique_together = ('user','school',)



def get_file_path(instance, filename):
    try:
      spl = filename.split('.')
      ext = spl[-1]
      orig_name = spl[-2][0:20]
    except:
      orig_name = ''
      ext = filename.split('.')[-1]

    filename = "%s_%s.%s" % (orig_name, uuid.uuid4(), ext)
    return os.path.join('userFiles', filename)


from boto.s3.connection import S3Connection, Bucket, Key

s3conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
s3b = Bucket(s3conn, settings.AWS_STORAGE_BUCKET_NAME)

from threading import Thread
def postpone(function):
  def decorator(*args, **kwargs):
    t = Thread(target = function, args=args, kwargs=kwargs)
    t.daemon = True
    t.start()
  return decorator

@postpone
def deleteS3File(filename):
  s3k = Key(s3b)
  s3k.key = filename
  s3b.delete_key(s3k)

def getS3contentType(filename, instance):
  # grabs file contentType from S3 
  # to be saved in db via instance

  k = s3b.get_key(filename)
  contentType = k.content_type

  # preserve original filename
  if len(instance.origFileName) > 0 and contentType.split('/')[0].lower() != 'image':
    k.set_remote_metadata(
      metadata_plus ={},
      metadata_minus ={},
      preserve_acl = True, 
      headers = {'Content-Disposition': 'attachment; filename="{}"'.format(instance.origFileName)})

  instance.contentType = contentType
  instance.save()

  return contentType

from django.contrib.postgres.fields import JSONField

def metadata_default():
    return {}

class UserFile(models.Model):
  user = models.ForeignKey('User')
  file  =  models.FileField(upload_to=get_file_path, blank = False )
  createdDate = models.DateTimeField(default=timezone.now)

  # this is the original filename before it is saved into AWS S3
  # filename length limit for windows is 260 chars, mac is 31
  origFileName = models.CharField(max_length = 260, blank=True, default="")
  metadata = JSONField(default = metadata_default)
  contentType = models.CharField(max_length = 100, blank=True, null=True)

  def set_origFileName(self):
    """
    set a deafult original file name that uses the S3 filename as a proxy
    """
    # skip function if origFileName is already set

    if len(self.origFileName) > 0:
      return
    fname = str(self.file).split('/')[-1]
    self.origFileName = fname
    self.save()

  def save(self, *args, **kwargs):
    # self.origFileName =  str(self.file)
    super(UserFile, self).save()

    # print str(self.file)
    # after initial save, the file should now be in S3, 
    # make a request to see what the assigned metadata is and save it back to DB
    if self.contentType is None:
      self.contentType = getS3contentType(str(self.file), self)



  def delete(self, *args, **kwargs):
    deleteS3File(self.file.name)
    super(UserFile, self).delete()




