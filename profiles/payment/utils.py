import braintree, datetime
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
# from profiles.models import Group, GroupMemberRelation, TraineeExpertRelation, Payment, Organization, OrganizationAuditTrail, ORG_TRAINEE, ORG_EXPERT, ORG_GROUPMEMBER

# print 'braintree',braintree

braintree.Configuration.configure(braintree.Environment.Sandbox,
                                  merchant_id=settings.BRAINTREE_MERCHANT_ID,
                                  public_key=settings.BRAINTREE_PUB_KEY,
                                  private_key=settings.BRAINTREE_PRIV_KEY)
