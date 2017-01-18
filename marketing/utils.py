from marketing.models import *
from profiles.models import School

import nltk


# from marketing.utils import *
# autoCleanSchoolsData()

def cleanSchoolsData():
	"""
	get a list of schools and try to mark them onto unclean marketing db users
	"""

	validSchoolsList = [ i['name'] for i in School.objects.all().values('name')]

	# only map empty ones

	for m in Marketing.objects.filter(guessSchool__isnull = True):
		m.cleanSchool(validSchoolsList)


def autoCleanSchoolsData():
	"""
	What would the computer guess based on models
	"""

	validSchoolsList = [ i['name'] for i in School.objects.all().values('name')]

	# only map empty ones

	for m in Marketing.objects.all():
		m.autoCleanSchool(validSchoolsList)


