import httplib2
import re

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run


class Calendar(object):
    def __init__(self, config, src_path):
        """
        :type src_path: str
        :type config: list of tuples
        """
        self.config = {}
        for key, value in config:
            self.config[key] = value
        self.user_agent = 'economic-py/0.3'
        self.ignore_events = self.config['ignore_events'].lower().split(',')

        # The client_id and client_secret can be found in Google Developers Console
        flow = OAuth2WebServerFlow(
            client_id=self.config['client_id'],
            client_secret=self.config['client_secret'],
            scope='https://www.googleapis.com/auth/calendar',
            user_agent=self.user_agent)

        # To disable the local server feature, uncomment the following line:
        # import gflags
        # FLAGS = gflags.FLAGS
        # FLAGS.auth_local_webserver = False

        # If the Credentials don't exist or are invalid, run through the native client
        # flow. The Storage object will ensure that if successful the good
        # Credentials will get written back to a file.
        storage = Storage(src_path + '/calendar.dat')
        credentials = storage.get()
        if credentials is None or credentials.invalid is True:
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

    def ignore_event(self, event):
        """
        Based on configuration return info whether event should be ignored.
        If task summary contains one of ignored phrases then whole event
        will be ignored.

        :param event:
        :type event: dict
        :return bool
        """
        ignore = False

        for ignore_event in self.ignore_events:
            if ignore_event and ignore_event in event['summary'].lower():
                ignore = True

        return ignore

    def get_events(self, start_date, end_date):
        """
        Get events from calendar between given dates.

        :param start_date: date in format YYYY-MM-DDTHH:MM:SSZ
        :param end_date:
        :type end_date: str
        :type start_date: str
        """
        page_token = None

        while True:
            events = self.service.events().list(calendarId='primary', pageToken=page_token, singleEvents=True,
                                                timeMin=start_date, timeMax=end_date).execute()
            for event in events['items']:
                if 'attendees' not in event:
                    print("SKIPPED (no attendees) - %s" % (event['summary']))
                    continue

                for attendee in event['attendees']:
                    if 'self' in attendee and attendee['responseStatus'] == 'accepted':
                        if 'dateTime' not in event['start'] or 'dateTime' not in event['end']:
                            print("SKIPPED (event without specific hours of start/end) - %s" % (event['summary']))
                            break
                        if event['start']['dateTime'][:10] != event['end']['dateTime'][:10]:
                            print("SKIPPED (event start and end days are different) - %s" % (event['summary']))
                            break
                        if not self.ignore_event(event):
                            yield {
                                'start_date': event['start']['dateTime'],
                                'end_date': event['end']['dateTime'],
                                'title': event['summary'].encode('utf8'),
                                'project_id': self.get_project_id(event.get('description', '')),
                                'activity_id': self.get_activity_id(event.get('description', ''))
                            }
                        else:
                            print('SKIPPED (contains ignored phrase) - %s' % event['summary'])
                        break
                else:
                    print("SKIPPED (not attending)- %s" % (event['summary']))
            page_token = events.get('nextPageToken')
            if not page_token:
                break

    def get_project_id(self, description):
        """
        Get e-conomic project ID from event description.
        Regexp pattern "project_id_pattern" from configuration is being used here.
        :type description: str
        :param description: description of meeting
        """
        if not self.config.get('project_id_pattern'):
            return -1

        result = re.search(self.config.get('project_id_pattern'), description.lower())
        if result:
            return int(result.groups()[0])

        return self.config.get('default_project_id', False)

    def get_activity_id(self, description):
        """
        Get e-conomic activity ID from event description.
        Regexp pattern "project_id_pattern" from configuration is being used here.

        Default activity ID specified in configuration will be returned
        if pattern search will not return any results.
        :type description: str
        :param description: description of meeting
        """
        if not self.config.get('activity_id_pattern'):
            return -1

        result = re.search(self.config.get('activity_id_pattern'), description.lower())
        if result:
            return int(result.groups()[0])

        return self.config.get('default_activity_id', False)
