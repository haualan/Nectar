from django.test import TestCase
from profiles.models import *

from course.models import Course


class ManualTransactTest(TestCase):
  def setUp(self):
    self.buyerUser = User.objects.create(username ='buyerUser', role='G')
    self.officeUser = User.objects.create(username ='officeUser', role='O')
    self.studentUser = User.objects.create(username ='studentUser', role='S')

    self.testCourse = Course.objects.create(course_code = 'testCourseCode')





  def test_create_manual_charge(self):
    """Manual charges can be created"""

    dummyTran = {
      u'currency': u'hkd',
      u'localCurrencyChargedAmount': 6600,
      u'buyerID': self.buyerUser.id,
      u'studentID': self.studentUser.id,
      u'course_code': self.testCourse.course_code,
      'source': 'CASH',
      'user': self.officeUser,

      'remarks': 'testmode',
    }

    openTrans = Ledger.createManualCharge(**dummyTran)

    self.assertEqual(openTrans.localCurrencyChargedAmount, 6600)
    self.assertIsNotNone(openTrans.order_id)

    return openTrans


  def test_create_manual_refund(self):
    """Manual charges can be created"""

    # need to have an open order and test cases must be independant
    openTrans = self.test_create_manual_charge()

    payload = {
      'localCurrencyChargedAmount': -3300, 
      'order_id': openTrans.order_id, 
      'source': 'CASH', 
      'user': self.officeUser, 
      'remarks': "testmode"
    }

    closingTrans = Ledger.createManualRefund(**payload)

    self.assertEqual(closingTrans.localCurrencyChargedAmount, -3300)

    return closingTrans

  


