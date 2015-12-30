from __future__ import print_function
import httplib2

from calendar import Calendar
from apiclient.discovery import build
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow


class CalendarGoogle(Calendar):
    """
    Class related to communication with Google Calendar using API V3.

    :param config: list
    :param src_path: str
    """

    def __init__(self, config, src_path, *args, **kwargs):
        """
            Set configuration and init variables.

            :type src_path: str
            :type config: list of tuples
            """
        super(CalendarGoogle, self).__init__(config, *args, **kwargs)
        self.event_summary_field = 'summary'
        self.event_attendees_field = 'attendees'
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
            credentials = tools.run(flow, storage)

        # Create an httplib2.Http object to handle our HTTP requests and authorize it
        # with our good Credentials.
        http = httplib2.Http()
        http = credentials.authorize(http)
        # Build a service object for interacting with the API. Visit
        # the Google Developers Console
        # to get a developerKey for your own application.
        self.service = build(serviceName='calendar', version='v3', http=http,
                             developerKey='notsosecret')

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
