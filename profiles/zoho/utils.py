import requests
from django.conf import settings






def insertZohoNoteByUser(subdomain, u, title="", text=""):
  """
  given a user u, will attempt to insert a note for this user by email.
  - will avoid creating the same user twice by looking at the email
  - can be used post-purchase to add a note for example.
  """

  zohoContactID = getZohoContactID(subdomain, u.email)

  if not zohoContactID:
    # user does not exist, so create the user and extract entity id
    r = createZohoContact(subdomain, u)
    zohoContactID = extractZohoContactIDFromResponse(r)


  if not zohoContactID:
    print 'could not access zoho id for this user, cannot add note...', u.email
    return


  return createZohoNote(subdomain = subdomain, entityId = zohoContactID, title = title, text = text)







def getZohoContactID(subdomain, email):
  """
  returns the contact ID if user exists otherwise None
  """
  r = searchZohoContactsByEmail(subdomain, email)

  if r.status_code == 200:
    resp = r.json()

    rows = resp.get('response', {}).get('result', {}).get('Contacts', {}).get('row', {})
    # in zoho if rows is an iterable, it has multiple results, take the first item and continue
    if type(rows) == list and len(rows) > 0:
      fl = rows[0].get('FL', [])
    else:
      fl = rows.get('FL', [])
    # if there were stuff in contents we would expect something like this
    #    [{u'content': u'1921877000001222001', u'val': u'CONTACTID'},
    # {u'content': u'selinananny@gmail.com', u'val': u'Email'}]


    cid = None
    for i in fl:
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

  # Lead Source as hummingbird

  ele = etree.SubElement(row, "FL", val='Lead Source')
  ele.text = 'hummingbird'


  for k, v in zohoUserContactsMap.iteritems():
    userAttr = getattr(u, k, None)
    if userAttr:
      ele = etree.SubElement(row, "FL", val=v)
      ele.text = userAttr

  return etree.tostring(contacts)





def createZohoNote(subdomain, entityId, title='', text=''):
  """
  given a entity (Lead or Contact), add a textual note to the person
  https://www.zoho.com/crm/help/api/insertrecords.html

  Insert notes and relate to the primary module
    XML Format:

    https://crm.zoho.com/crm/private/xml/Notes/insertRecords?newFormat=1&authtoken=Auth Token
    &scope=crmapi
    &xmlData=

    <Notes>

    <row no="1">

    <FL val="entityId">2000000078001</FL>

    <FL val="Note Title">Zoho CRM Sample Note</FL>

    <FL val="Note Content">This is sample content to test Zoho CRM API</FL>

    </row>

    </Notes>
  """

  notes = etree.Element("Notes")
  row = etree.SubElement(notes, "row", no="1")

  # elements that need to be inserted to record
  ele = etree.SubElement(row, "FL", val='entityId')
  ele.text = entityId

  ele = etree.SubElement(row, "FL", val='Note Title')
  ele.text = title

  ele = etree.SubElement(row, "FL", val='Note Content')
  ele.text = text


  xmlPayload = etree.tostring(notes)

  key = settings.ZOHO_KEY_MAP.get(subdomain, None)
  if not key:
    key = settings.ZOHO_KEY_MAP.get('hk')


  r = requests.post(url = 'https://crm.zoho.com/crm/private/xml/Notes/insertRecords?authtoken={}&scope=crmapi&xmlData={}'.format(key, xmlPayload) )

  return r






def createZohoContact(subdomain, u):
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

  key = settings.ZOHO_KEY_MAP.get(subdomain, None)
  if not key:
    key = settings.ZOHO_KEY_MAP.get('hk')

  r = requests.post(url = 'https://crm.zoho.com/crm/private/xml/Contacts/insertRecords?authtoken={}&scope=crmapi&newFormat=1&xmlData={}'.format(key, xmlPayload) )

  return r


from lxml import objectify
def extractZohoContactIDFromResponse(r):
  """
  given a response r fom zoho contacts api creation, extract the id,
  return None if broken
  """

  if r.status_code != 200:
    return None

  tree = objectify.fromstring('{}'.format(r.text))
  records = tree.result.recorddetail.getchildren()

  for i in records:
    if i.attrib.get('val', None) == 'Id':
      return i.text


  # id not found
  return None





def searchZohoContactsByEmail(subdomain, email):
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

  key = settings.ZOHO_KEY_MAP.get(subdomain, None)
  if not key:
    key = settings.ZOHO_KEY_MAP.get('hk')

  r = requests.get(
    url = 'https://crm.zoho.com/crm/private/json/Contacts/getSearchRecordsByPDC?authtoken={}&scope=crmapi&selectColumns=Contacts(Email)&searchColumn=email&searchValue={}'.format(key, email))

  return r