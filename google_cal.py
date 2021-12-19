from __future__ import print_function
from Adafruit_Thermal import *
import config
from datetime import datetime, timedelta
import pickle
import os.path
import dateutil.parser
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def main():
    p = Adafruit_Thermal()
    p.setDefault()
    p.setSize('L')
    p.println('Calendar')

    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    now = datetime.utcnow().isoformat() + 'Z'
    timeMax = (datetime.utcnow() +
               timedelta(days=config.calendar_days)).isoformat() + 'Z'
    event_results = service.events().list(calendarId='primary', timeMin=now,
                                          timeMax=timeMax, singleEvents=True, orderBy='startTime').execute()
    events = event_results.get('items', [])

    p.setSize('M')
    if not events:
        p.println("Nothing to do... chill out!")

    for event in events:
        # print(event)
        start_d_in = event['start'].get('date')
        start_dt_in = event['start'].get('dateTime')

        start_t_out = None
        if start_dt_in is not None:
            start_dt = dateutil.parser.parse(start_dt_in)
            start_d_out = start_dt.strftime(config.date_format)
            start_t_out = start_dt.strftime(config.time_format)
        else:
            start_d_out = dateutil.parser.parse(
                start_d_in).strftime(config.date_format)

        p.boldOn()
        p.underlineOn()
        p.justify('L')
        if start_t_out is not None:
            p.print(start_t_out)
            p.print(' ')

        p.println(start_d_out)
        p.boldOff()
        p.underlineOff()

        p.justify('R')
        p.println(event['summary'])

    p.setDefault()
    p.sleep()

main()
