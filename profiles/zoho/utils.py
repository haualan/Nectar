import requests
from django.conf import settings

def getZohoContactID(email):
  """
  returns the contact ID if user exists otherwise None
  """
  r = searchZohoContactsByEmail(email)

  if r.status_code == 200:
    resp = r.json()
    contents = resp.get('response', {}).get('result', {}).get('Contacts', {}).get('row', {}).get('FL', [])
    # if there were stuff in contents we would expect something like this
    #    [{u'content': u'1921877000001222001', u'val': u'CONTACTID'},
    # {u'content': u'selinananny@gmail.com', u'val': u'Email'}]


    cid = None
    for i in contents:
      if i.get('val', None) == 'CONTACTID':
        # return the ID when we hit it
        return i.get('content')

    # otherwise no record found
    return None

  # all other cases suggests either zoho is broken or no records are found
  return None

from lxml import etree

zohoUserContactsMap = {
  # <fca user attribute>: <zoho contacts FL attribute>
  'firstname': 'First Name',
  'lastname': 'Last Name',
  'email': 'Email',
  'phoneNumber': 'Phone',
}


def user_to_zohoContactXML(u):
  """
  given a user u 

  return something like:

  <Contacts>
  <row no="1">
  <FL val="First Name">Scott</FL>
  <FL val="Last Name">James</FL>
  <FL val="Email">test@test.com</FL>
  <FL val="Department">CG</FL>
  <FL val="Phone">999999999</FL>
  <FL val="Fax">99999999</FL>
  <FL val="Mobile">99989989</FL>
  <FL val="Assistant">John</FL>
  </row>
  </Contacts>


  """

  contacts = etree.Element("Contacts")
  row = etree.SubElement(contacts, "row", no="1")

  # row = contacts.append( etree.Element("row", no="1") )

  for k, v in zohoUserContactsMap.iteritems():
    userAttr = getattr(u, k, None)
    if userAttr:
      ele = etree.SubElement(row, "FL", val=v)
      ele.text = userAttr

  return etree.tostring(contacts)









def createZohoContact(u):
  """
  when passed a user, u, create a zoho contact:
  https://www.zoho.com/crm/help/api/insertrecords.html

  must insert as xml, sigh.... zoho

  https://crm.zoho.com/crm/private/xml/Contacts/insertRecords?authtoken=AuthToken&scope=crmapi&xmlData=Your XML Data 

  https://crm.zoho.com/crm/private/xml/Contacts/insertRecords?authtoken=Auth Token&scope=crmapi
  &newFormat=1
  &xmlData=

  <Contacts>
  <row no="1">
  <FL val="First Name">Scott</FL>
  <FL val="Last Name">James</FL>
  <FL val="Email">test@test.com</FL>
  <FL val="Department">CG</FL>
  <FL val="Phone">999999999</FL>
  <FL val="Fax">99999999</FL>
  <FL val="Mobile">99989989</FL>
  <FL val="Assistant">John</FL>
  </row>
  </Contacts>

  """
  xmlPayload = user_to_zohoContactXML(u)

  r = requests.post(url = 'https://crm.zoho.com/crm/private/xml/Contacts/insertRecords?authtoken={}&scope=crmapi&newFormat=1&xmlData={}'.format(settings.ZOHO_KEY, xmlPayload) )

  return r



def searchZohoContactsByEmail(email):
  """
  looks at zoho crm Contacts module for this email (belonging to parent or student)
  example response:
  In [3]: r = requests.get(url = 'https://crm.zoho.com/crm/private/json/Contacts/getSearchRecordsByPDC?authtoken=58fa737357803d76ee76ddec11556509&scope=crmapi&selectColumns=Contacts(Email)&searchColumn=email&searchValue=selinananny@gmail.com')

  In [4]: r.json()
  Out[4]:
  {u'response': {u'result': {u'Contacts': {u'row': {u'FL': [{u'content': u'1921877000001222001',
         u'val': u'CONTACTID'},
        {u'content': u'selinananny@gmail.com', u'val': u'Email'}],
       u'no': u'1'}}},
    u'uri': u'/crm/private/json/Contacts/getSearchRecordsByPDC'}}

  .... if no results
  In [5]: r.json()
  Out[5]:
  {u'response': {u'nodata': {u'code': u'4422',
     u'message': u'There is no data to show'},
    u'uri': u'/crm/private/json/Contacts/getSearchRecordsByPDC'}}

  """

  r = requests.get(
    url = 'https://crm.zoho.com/crm/private/json/Contacts/getSearchRecordsByPDC?authtoken={}&scope=crmapi&selectColumns=Contacts(Email)&searchColumn=email&searchValue={}'.format(settings.ZOHO_KEY, email))

  return r