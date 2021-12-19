from __future__ import print_function

from Adafruit_Thermal import *

import config

from datetime import datetime, timedelta
import dateutil.parser
import pickle
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/tasks.readonly']

def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('tasks', 'v1', credentials=creds)

        tasklists = service.tasklists().list(maxResults=10).execute().get('items', [])

        p = Adafruit_Thermal()
        p.setDefault()
        p.setSize('M')
	p.justify('C')

        if not tasklists:
            p.println('No task lists found.')
            return
        else:
            p.println('Tasks')

	p.setSize('S')

#        print('Task lists:')
        for tasklist in tasklists:
#            print(u'{0} ({1})'.format(tasklist['title'], tasklist['id']))

            tasks = service.tasks().list(
                tasklist=tasklist['id']).execute().get('items', [])
            for task in sorted(tasks, key=lambda t: t.get('order', '')):
		task_title = task.get('title', '-')
		task_status = task.get('status', None)
		task_due = task.get('due', None)

		if task_due is not None:
		    task_due_s = dateutil.parser.parse(task_due).strftime(config.date_format)
                    p.boldOn()
                    p.underlineOn()
 		    p.justify('R')
                    p.println(task_due_s)

		p.boldOff()
                p.underlineOff()
                p.justify('L')
		p.print('[ ] ')

                p.println(task_title)
        p.println('') # make some space

    except HttpError as err:
        print(err)


if __name__ == '__main__':
    main()
