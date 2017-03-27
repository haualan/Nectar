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

from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

import stripe

from django.contrib.postgres.fields import JSONField

# from activities.statistics.heartratemodel.utils import *
# from activities.statistics.jackdaniels import calc_JD_pace_heartrate

from botocore.utils import merge_dicts

from payment.utils import encodeReferralCode

from .utils import *

def metadata_default():
    return {}


gender_choices = (
      ('M', 'male'),
      ('F', 'female'),
  )

role_choices = (
      ('G', 'guardian'),
      ('S', 'student'),
      # instructor is a role set by system only
      ('I', 'instructor'),
      ('O', 'operations'),
      ('C', 'Chief Whatevers'),
  )
import pytz
tzName_choices = set((i, i) for i in pytz.all_timezones)

def get_eighteen_yearoldDate():
  return datetime((timezone.now().year - 18), 1, 1)

def get_default_age():
  return datetime((timezone.now().year - 30), 1, 1)

# DEFAULT_PROFILE_PICTURE_URL = 'http://placehold.it/350x350'
DEFAULT_PROFILE_PICTURE_URL = 'https://s3-ap-southeast-1.amazonaws.com/fcanectar/customMedia/defaultUserIcon.png'
DEFAULT_PROFILE_PICTURE_MALE_URL = 'https://s3-ap-southeast-1.amazonaws.com/fcanectar/customMedia/defaultUserIconBoy.png'



class User(AbstractEmailUser):
  avatar_url = models.URLField('avatar_url',blank=True, default=DEFAULT_PROFILE_PICTURE_URL)
  birth_date = models.DateField('birth_date', blank=True, default=get_default_age)
  gender = models.CharField('gender', max_length=1, default='M', choices = gender_choices)
  firstname = models.CharField('firstname', max_length=255, blank=True)
  lastname = models.CharField('lastname', max_length=255, blank=True)

  username = models.CharField('username', max_length=255, blank=False, null=True)
  email = models.EmailField(_('email address'), max_length=255, unique=True, null=True, blank=False)

  # timezone offset relative to UTC
  tzName = models.CharField(max_length=100, default = 'Hongkong',  choices = tzName_choices)
  phoneNumber = models.CharField(max_length=50, blank=True, null=False, default="")
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

  # the current school the user belongs to
  school = models.ForeignKey('School', null=True, default=None)


  # payment info
  stripeCustomerId = models.CharField(max_length=50, blank=False, null=True)
  # which stripe acct processed this, use contents to lookup stripe key in conifg
  stripeAcct = models.CharField(max_length=30, blank=False, null=True)

  # parent specific settings
  address = models.TextField(blank=True)
  addressGoogleRef = JSONField(default = metadata_default)

  # does your student need a computer?
  needComputer = models.BooleanField(default = False)

  # health remarks
  remarks = models.TextField(blank=True)

  # where did you hear about fca
  heardFrom = models.TextField(blank=True)

  # where did you specifically hear about fca (fixed options on frontend)
  # ex. google
  # facebook
  # printed ads
  heardFromOption = models.CharField(max_length=20, blank=True)

  # is a miscellaneous field for client side data 
  clientDump = JSONField(default = metadata_default)




  def save(self, clearClientDump=False, *args, **kwargs ):
    if self.clientDump and self.pk is not None and clearClientDump == False:
      # if clientDump has something (non-empty) and it is an existing value (not a new creation), 
      

      prevClientDump = User.objects.get(pk = self.pk).clientDump

      # attempt to merge with existing clientDump, 
      # merge_dicts will modify existing variable
      merge_dicts(self.clientDump, prevClientDump)


    if self.email == '':
      self.email = None

    if self.avatar_url in (DEFAULT_PROFILE_PICTURE_URL, DEFAULT_PROFILE_PICTURE_MALE_URL,):
      if self.gender == 'M':
        self.avatar_url = DEFAULT_PROFILE_PICTURE_MALE_URL
      else:
        self.avatar_url = DEFAULT_PROFILE_PICTURE_URL


    if self.email and self.stripeCustomerId and self.stripeAcct:
      self.updateStripeCustomer()

    super(User, self).save(*args, **kwargs) # Call the "real" save() method.


  def clearClientDump(self):
    self.clientDump = {}
    self.save(clearClientDump=True)


  def preferredSubdomain(self):
    """
    from clientDump try to guess what is the preferred subdomain of this user, if none, fall back to HK
    """
    subdomain = None

    if self.lon and self.lat:
      subdomain = get_closestSubdomainByCoord(lon = self.lon, lat = self.lat)
      return subdomain

    if self.clientDump != {}:
      course_code = self.clientDump.get('course_code', None)
      if course_code:
        from course.models import Course
        c = Course.objects.filter(course_code = course_code)
        if c:
          c = c.first()
          subdomain = c.subdomain
          return subdomain

    # by default return hong hong
    return 'hk'





  def updateStripeCustomer(self):
    """
    updates customer attrbutes in Stripe
    """
    if not self.stripeCustomerId:
      # if there is no stripe info, do nothing
      return False

    if self.stripeAcct not in settings.STRIPE_SECRET_MAP:
      # if there is no valid strip acct info, do nothing
      # because it's unclear which stripeAcct to lookup
      return False

    try:
      stripe.api_key = settings.STRIPE_SECRET_MAP.get( self.stripeAcct )
      cu = stripe.Customer.retrieve(self.stripeCustomerId)
      cu.metadata = { 'uid': self.id }
      cu.email = self.email
      cu.save()
    except stripe.InvalidRequestError, e:
      print 'updateStripeCustomer error', e

      # stripe ID probably bad, discard henceforth
      self.stripeCustomerId = None
      self.stripeAcct = None



    return True





  

  @property
  def get_mySchools(self):
    """
    returns groups of which this user is a member of
    """
    return School.objects.filter(userschoolrelation__user = self).order_by('name')

  @property
  def get_myStudents(self):
    """
    returns students affiliated with current user, regardless of role
    """
    return User.objects.filter(id__in =  self.guardianstudentrelation_set.values('student'))


  @property
  def get_myActiveStudents(self):
    """
    returns students affiliated with current user, regardless of role
    """
    return User.objects.filter(is_active = True, id__in =  self.guardianstudentrelation_set.values('student'))


  def createMyStudentRelation(self, targetUser):
    """
    forms a student relationship with another user
    """

    return self.guardianstudentrelation_set.create(student = targetUser )


  def isMyStudent(self, targetUser ):
    return self.guardianstudentrelation_set.filter(student = targetUser ).exists()

  @property
  def get_myProjects(self):
    """
    returns this user's uploaded apps
    """
    return self.project_set.all().order_by('updated')

  @property
  def get_myEnrolledCourses(self):
    """
    returns this user's enrolled courses
    """
    return self.usercourserelationship_set.all()

  @property
  def get_myTrophyRecords(self):
    """
    returns this user's trophy records
    """
    return self.trophyrecord_set.all()

  @property
  def get_myReactions(self):
    """
    returns this user's recieved reactions / loves / likes by other users
    """
    return self.trophyrecordaction_set.model.objects.filter(trophyRecord__user = self)

  def get_age(self):
    today = datetime.now()
    return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

  def get_full_name(self):
    return self.name




  def __unicode__(self):
    # return self.id
    if self.email is not None:              
      return self.email

    if self.username is not None:              
      return self.username

    return str(self.id)

  @property
  def name(self):
    return u'{} {}'.format(self.firstname, self.lastname)

  @property
  def displayName(self):
    fname = self.firstname
    lname = self.lastname
    email = self.email
    username = self.username

    # if avatar name exists, should be returned here

    if len(fname) > 0 and len(lname) > 0:
        return u'{} {}'.format(fname, lname)

    if len(fname) > 0:
        return fname

    if len(lname) > 0:
        return lname

    if username:
      return username

    if email:
      return email
    # email is always the fallback for name display
    return ''

  @property
  def slugName(self):
    return slugify(self.displayName , allow_unicode=True)

  @property
  def referralCode(self):
    """ returns this user's referral code """
    return encodeReferralCode(self.id)

  def send_referral_email(self, emailStr):
    """
    sends a referral email to a string of email recipients separated by comma
    """
    send_referral_email(self, emailStr)


  class Meta:
    unique_together = ('username',)




class UserForm(ModelForm):
  """
  This is the form fields showing fields a user is allowed to change
  """
  class Meta:
    model = User
    fields = ['email', 'username', 'firstname','lastname', 'avatar_url', 'birth_date', 'gender', 'isSearchable']



class UserReferral(models.Model):
  user = models.ForeignKey('User')
  email = models.EmailField()
  createdDate = models.DateTimeField(default=timezone.now)

  class Meta:
    # user can only send email once
    unique_together = ('user', 'email')
    


class GuardianStudentRelation(models.Model):
  guardian = models.ForeignKey('User')
  student = models.ForeignKey('User', related_name='GuardianStudentRelation_student')  

  def __unicode__(self):
    return u'Guardian: %s Student: %s' % (self.guardian, self.student)

  class Meta:
    unique_together = ('guardian', 'student',)


DEFAULT_SCHOOL_PICTURE_URL = 'https://s3-ap-southeast-1.amazonaws.com/fcanectar/customMedia/schoolIcon.png'
class School(models.Model):
  avatar_url = models.URLField('avatar_url',blank=True, default=DEFAULT_SCHOOL_PICTURE_URL)
  name = models.CharField(max_length=255, blank=False)
  lon = models.DecimalField(max_digits=9, decimal_places=6, null=True)
  lat = models.DecimalField(max_digits=9, decimal_places=6, null=True)
  formatted_address = models.CharField(max_length=255, null=True)

  # this is a google place_id for google places API
  place_id = models.CharField(max_length=255, null=True, unique=True)


  class Meta:
    # schools must be unique
    unique_together = ('name',)



# class UserSchoolRelation(models.Model):
#   user = models.ForeignKey('User')
#   school = models.ForeignKey('School')
#   enrollmentDate = models.DateField(blank=True, auto_now_add=True)


#   class Meta:
#     # each user can be associated to multiple schools but only once
#     unique_together = ('user','school',)



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


from payment.models import *

