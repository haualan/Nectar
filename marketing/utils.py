from marketing.models import *
from profiles.models import School

import nltk

def cleanSchoolsData():
	"""
	get a list of schools and try to mark them onto unclean marketing db users
	"""

	validSchoolsList = [ i['name'] for i in School.objects.all().values('name')]


	
