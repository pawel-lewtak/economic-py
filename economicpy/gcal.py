from __future__ import print_function
import httplib2
import re

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run


class Calendar(object):

    """
    Class related to communication with Google Calendar using API V3.

    :param config: list
    :param src_path: str
    """

    def __init__(self, config, src_path):
        """
        Set configuration and init variables.

        :type src_path: str
        :type config: list of tuples
        """
        self.config = {}
        for key, value in config:
            self.config[key] = value
        self.user_agent = 'economic-py/0.3'
        self.ignore_events = self.config['ignore_events'].lower().split(',')
        if self.config.get('mock_enabled', False):
            return

        self.service = None
        self.login(src_path)

    def login(self, src_path):
        """
        Login to Google API using data provided in config.

        :param src_path: path to calendar credentials
        :type src_path: str
        """
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

    @staticmethod
    def verify_dates(event):
        """
        Verify start and end dates of event.

        Event should have specific hours and same day of start and end.

        :param event: dict
        :return: bool
        """
        if 'dateTime' not in event['start'] or 'dateTime' not in event['end']:
            print("SKIPPED (event without specific hours of start/end) - %s" % (event['summary']))
            return False

        if event['start']['dateTime'][:10] != event['end']['dateTime'][:10]:
            print("SKIPPED (event start and end days are different) - %s" % (event['summary']))
            return False

        return True

    @staticmethod
    def get_events_with_attendees(events):
        """
        From given list of events filter out events without atendees.

        :param events: list
        :return: list
        """
        output = []
        for event in events:
            if 'attendees' in event:
                output.append(event)
            else:
                print("SKIPPED (no attendees) - %s" % (event['summary']))

        return output

    @staticmethod
    def get_accepted_events(events):
        """
        From given list of events filter out events that are not accepted by current user.

        :param events: list
        :return: list
        """
        output = []
        for event in events:
            for attendee in event['attendees']:
                if 'self' in attendee:
                    if attendee['responseStatus'] == 'accepted':
                        output.append(event)
                    else:
                        print("SKIPPED (not attending) - %s" % (event['summary']))

        return output

    def get_events_with_proper_dates(self, events):
        """
        Filter out events with bad start/end date.

        As bad start/end date is considered date without time
        or or event spanning over many days.
        :param events: list
        :return: list
        """
        output = []
        for event in events:
            if self.verify_dates(event):
                output.append(event)
            else:
                print("SKIPPED (dates issue) - %s" % (event['summary']))

        return output

    def skip_ignored_events(self, events):
        """
        From given list of events filter out events that are ignored.

        Event is ignored if it contains any of phrases defined in configuration.

        :param events: list
        :return: list
        """
        output = []
        for event in events:
            if not self.ignore_event(event):
                output.append(event)
            else:
                print('SKIPPED (contains ignored phrase) - %s' % event['summary'])

        return output

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
            original_events = self.service.events().list(calendarId='primary', pageToken=page_token, singleEvents=True,
                                                         timeMin=start_date, timeMax=end_date).execute()
            events = self.get_events_with_attendees(original_events['items'])
            events = self.get_accepted_events(events)
            events = self.skip_ignored_events(events)
            events = self.get_events_with_proper_dates(events)
            for event in events:
                yield {
                    'start_date': event['start']['dateTime'],
                    'end_date': event['end']['dateTime'],
                    'title': event['summary'].encode('utf8'),
                    'project_id': self.get_project_id(event.get('description', '')),
                    'activity_id': self.get_activity_id(event.get('description', ''))
                }
            page_token = original_events.get('nextPageToken')
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
