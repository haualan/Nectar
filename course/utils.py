
from uploadApp.models import *
from course.models import *
from django.db.models import Avg, Case, Count, F, Max, Min, Prefetch, Q, Sum, When

# from course.models import UserCourseRelationship

languages = [i[0] for i in language_choices]

def updateTrophyRecord(user):
	"""
	given a user, check if new tropy records should be added according to the trophy model
	"""

	print 'updateTrophyRecord', user.id, user.email

	# currentTrophies = Trophy.objects.all()

	# record all active apps uploaded and points awarded 
	activeProjects = user.project_set.annotate(
		Count('projectsourcefile')
	).filter(
		Q(projectsourcefile__purpose = 'package') | Q(projectsourcefile__purpose = 'source'),
		projectsourcefile__count__gte = 1
	)

	# these are the projected points from apps uploaded
	languagesPoints = {}
	for p in activeProjects:
		if p.language in languagesPoints:
			languagesPoints[p.language] += 1
		else:
			languagesPoints[p.language] = 1

	print languagesPoints

	# compare the projected points against the trophy thresholds for those particular langues
	languageTrophies = Trophy.objects.exclude(language='')

	# expected language trophies
	expectedLangTrophies = set()

	for l in languageTrophies:
		# for each language trophy see if the threshold is met or exceeded
		if l.language in languagesPoints and languagesPoints[l.language] >= l.threshold:
			# if it is met or exceeded, show trophies that are earned, keep a list of earned trophies
			expectedLangTrophies.add(l.id)


	# compare the expectedLangTrophyRecs with the current trophy record of the user
	currentTrophyRec = set([i.trophy.id for i in user.trophyrecord_set.filter(trophy__in = expectedLangTrophies)])

	# find the set of missing trophies that are expected but not in currentTrophyRec
	missingTrophies = expectedLangTrophies.difference(currentTrophyRec)


	# iterate and add these missingTrophies
	for i in missingTrophies:
		# i is a trophy_id
		TrophyRecord.objects.create(user = user, trophy_id=int(i) )

	# take care of challenge records now
	challengeTrophies = Trophy.objects.filter(language='')



	# these are the earned points already in trophy record
	# languageChallengeRecords = user.challengerecord_set.filter(language_isnull = False)



	# collect all languages and loop thru one by one
	# for l in languages:
	# 	for p in activeProjects:
	# 		if p.language == l:
				# if the languages match, assign trophy model
				# assume every active projects earns 1 point for that language


def sampleChallenge():
	"""
	generates a skeleton for challenges
	"""

	p = {
		'topic':'Postcard',
		'media':[
			# artwork for this challenge or group of questions
			'https://media.kahoot.it/5e1a14b6-6aa5-4c3c-8ba8-069c4336becd',
			
		], 
		'questions':[
			{
				'type': 'multipleChoice',
				'answerKey': 'a',
				'media': [
					'https://media.kahoot.it/1f160791-6512-4f8a-af33-5ed49d23711a',
				],
				'choices': {
					'a':"It clears our app of drawn lines",
					'b':"It doesn't do anything",
					'c':"it clears our variable",
					'd':"It clears our pen color",
				}
			},
			{
				'type': 'multipleChoice',
				'answerKey': 'a',
				'choices': {
					'a':"A procedure",
					'b':"An event",
					'c':"A loop",
					'd':"A motion block",
				}
			},


		]

	}

	return p











