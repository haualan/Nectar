
from uploadApp.models import *
from course.models import *

# from course.models import UserCourseRelationship

languages = [i[0] for i in language_choices]

def updateTrophyRecord(user):
	"""
	given a user, check if new tropy records should be added according to the trophy model
	"""

	print 'updateTrophyRecord', user.id, user.email

	currentTrophies = Trophy.objects.all()

	# record all active apps uploaded and points awarded 
	activeProjects = user.project_set.annotate(
		Count('projectsourcefile')
	).filter(
		projectsourcefile__count__gte = 1
	)

	# these are the projected points from apps uploaded
	languagesPoints = {}
	for p in activeProjects:
		if p.language in languagesPoints:
			languagesPoints[p.language] += 1
		else:
			languagesPoints[p.language] = 0

	print languagesPoints

	# compare the projected points against the trophy thresholds for those particular langues
	languageTrophies = Trophy.objects.filter(language_isnull=False)

	# these are the earned points already in trophy record
	# languageChallengeRecords = user.challengerecord_set.filter(language_isnull = False)



	# collect all languages and loop thru one by one
	# for l in languages:
	# 	for p in activeProjects:
	# 		if p.language == l:
				# if the languages match, assign trophy model
				# assume every active projects earns 1 point for that language






