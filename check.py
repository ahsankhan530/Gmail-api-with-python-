from apiclient import discovery
from apiclient import errors
from httplib2 import Http
from oauth2client import file, client, tools
import base64
from bs4 import BeautifulSoup
# import dateutil.parser as parser
import csv
import re
import pandas as pd
from time import strftime, gmtime
import sys
from flask import Flask,render_template
def ReadEmailDetails(service, user_id, msg_id):

  temp_dict = { }

  try:

      message = service.users().messages().get(userId=user_id, id=msg_id).execute() # fetch the message using API
      payld = message['payload'] # get payload of the message
      headr = payld['headers'] # get header of the payload


      for one in headr: # getting the Subject
          if one['name'] == 'Subject':
            msg_subject = one['value']
            temp_dict['Subject'] = msg_subject

          else:
              pass


      for two in headr: # getting the date
          if two['name'] == 'Date':
              msg_date = two['value']
              # date_parse = (parser.parse(msg_date))
              # m_date = (date_parse.datetime())
              temp_dict['DateTime'] = msg_date
          else:
              pass

      
      email_parts = payld['parts'] # fetching the message parts
      part_one  = email_parts[0] # fetching first element of the part
      part_body = part_one['body'] # fetching body of the message
      part_data = part_body['data'] # fetching data from the body
      clean_one = part_data.replace("-","+") # decoding from Base64 to UTF-8
      clean_one = clean_one.replace("_","/") # decoding from Base64 to UTF-8
      clean_two = base64.b64decode (bytes(clean_one, 'UTF-8')) # decoding from Base64 to UTF-8
      soup = BeautifulSoup(clean_two , "lxml" )
      message_body = soup.body()
      # message_body is a readible form of message body
      # depending on the end user's requirements, it can be further cleaned
      # using regex, beautiful soup, or any other method
      temp_dict['Message_body'] = message_body

  except Exception as e:
      print(e)
      temp_dict = None
      pass

  finally:
      return temp_dict


def ListMessagesWithLabels(service, user_id, label_ids=[]):
  try:
    response = service.users().messages().list(userId=user_id,
                                               q="Simon",
                                               maxResults=500).execute()
    respons = service.users().messages().list(userId=user_id,
                                               q="Daraz",
                                               maxResults=500).execute()

    messages = []
    if 'messages' in response or respons:
      messages.extend(response['messages'])
      messages.extend(respons['messages'])

    while 'nextPageToken' in response :
      page_token = response['nextPageToken']

      response = service.users().messages().list(userId=user_id,pageToken=page_token,q="Simon").execute()
      respons = service.users().messages().list(userId=user_id,pageToken=page_token,q="Daraz").execute()

      messages.extend(response['messages'])
      messages.extend(respons['messages'])

      # print('... total %d emails on next page [page token: %s], %d listed so far' % (len(response['messages']), page_token, len(messages)))
      sys.stdout.flush()

    return messages

  except errors.HttpError as error:
    print('An error occurred: %s' % error)


if __name__ == "__main__":
  print('\n... start')

  # Creating a storage.JSON file with authentication details
  SCOPES = 'https://www.googleapis.com/auth/gmail.modify' # we are using modify and not readonly, as we will be marking the messages Read
  store = file.Storage('a.json')
  creds = store.get()

  if not creds or creds.invalid:
      flow = client.flow_from_clientsecrets('secret.json', SCOPES)
      creds = tools.run_flow(flow, store)

  GMAIL = discovery.build('gmail', 'v1', http=creds.authorize(Http()))
  print("GMAIL",GMAIL['logger'])
  user_id =  'me'
 

  # print('\n... list all emails')

  # email_list = ListMessagesWithLabels(GMAIL, user_id, [label_id_one,label_id_two])  # to read unread emails from inbox
  email_list = ListMessagesWithLabels(GMAIL, user_id, [])

  final_list = [ ]

  print('\n... fetching all emails data, this will take some time')
  sys.stdout.flush()


  #exporting the values as .csv
  rows = 0
  with open('s.csv', 'w', encoding='utf-8', newline = '') as csvfile:
      fieldnames = ['Subject','DateTime','Message_body']

      writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter = ',')
      writer.writeheader()

      for email in email_list:
        msg_id = email['id'] # get id of individual message
        email_dict = ReadEmailDetails(GMAIL,user_id,msg_id)

        if email_dict is not None:
          writer.writerow(email_dict)
          rows += 1

        if rows > 0 and (rows%50) == 0:
          # print('... total %d read so far' % (rows))
          sys.stdout.flush()

  # print('... emails exported into %s' % (file))
  # print("\n... total %d message retrived" % (rows))
  sys.stdout.flush()

  # print('... all Done!')
  df=pd.read_csv('s.csv')
  a=df['Unnamed: 0']
  q=[]
  for i in a:
    if '$' in i:
      temp = re.findall(r'\d+', i) 
      for w in temp:
        c = int(w)
        q.append(c)
  q=sum(q)
  print(q)
