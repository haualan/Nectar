from course.models import *


def updateTrophyRecord(user):
	"""
	given a user, check if new tropy records should be added according to the trophy model
	"""

	print 'updateTrophyRecord', user.id, user.email

	currentTrophies = Trophy.objects.all()