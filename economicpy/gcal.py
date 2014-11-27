import gflags
import httplib2

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run


class Calendar(object):
    def __init__(self, client_id, client_secret, ignore_events):
        self.user_agent = 'economic-py/0.3'
        self.ignore_events = ignore_events
        FLAGS = gflags.FLAGS

        # The client_id and client_secret can be found in Google Developers Console
        flow = OAuth2WebServerFlow(
            client_id=client_id,
            client_secret=client_secret,
            scope='https://www.googleapis.com/auth/calendar',
            user_agent=self.user_agent)

        # To disable the local server feature, uncomment the following line:
        # FLAGS.auth_local_webserver = False

        # If the Credentials don't exist or are invalid, run through the native client
        # flow. The Storage object will ensure that if successful the good
        # Credentials will get written back to a file.
        storage = Storage('calendar.dat')
        credentials = storage.get()
        if credentials is None or credentials.invalid == True:
            credentials = run(flow, storage)

        # Create an httplib2.Http object to handle our HTTP requests and authorize it
        # with our good Credentials.
        http = httplib2.Http()
        http = credentials.authorize(http)

        # Build a service object for interacting with the API. Visit
        # the Google Developers Console
        # to get a developerKey for your own application.
        self.service = build(serviceName='calendar', version='v3', http=http,
                             developerKey='notsosecret')

    def get_events(self, start_date, end_date):
        """
        Get events from calendar between given dates.
        """
        page_token = None

        while True:
            events = self.service.events().list(calendarId='primary', pageToken=page_token, singleEvents=True,
                                                timeMin=start_date, timeMax=end_date).execute()
            for event in events['items']:
                if event['status'] == "confirmed" and event['summary'] not in self.ignore_events:
                    yield {
                        'start_date': event['start']['dateTime'],
                        'end_date': event['end']['dateTime'],
                        'title': event['summary'].encode('utf8')
                    }
            page_token = events.get('nextPageToken')
            if not page_token:
                break
