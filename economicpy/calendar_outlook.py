from __future__ import print_function
from calendar import Calendar
import requests
import json


class CalendarOutlook(Calendar):
    """
    Class related to communication with Google Calendar using API V3.

    :param config: list
    """

    def __init__(self, config, *args, **kwargs):
        """
        Set configuration and init variables.

        :type config: list of tuples
        """
        super(CalendarOutlook, self).__init__(config, *args, **kwargs)
        self.rest_api_url = 'https://outlook.office365.com/api/v1.0/me/calendarview?startDateTime=%s&endDateTime=%s'
        self.event_summary_field = 'Subject'
        self.event_attendees_field = 'Attendees'

    @staticmethod
    def verify_dates(event):
        """
        Verify start and end dates of event.

        Event should have specific hours and same day of start and end.

        :param event: dict
        :return: bool
        """
        if event['Start'][:10] != event['End'][:10]:
            print("SKIPPED (event start and end days are different) - %s" % (event['Subject']))
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
            if 'ResponseStatus' in event:
                if event['ResponseStatus']['Response'] == 'Accepted':
                    output.append(event)
                else:
                    print("SKIPPED (not attending) - %s" % (event['Subject']))

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
                print("SKIPPED (dates issue) - %s" % (event['Subject']))

        return output

    def get_events(self, start_date, end_date):
        """
        Get events from calendar between given dates.

        :param start_date: date in format YYYY-MM-DDTHH:MM:SSZ
        :param end_date: date in format YYYY-MM-DDTHH:MM:SSZ
        :type end_date: str
        :type start_date: str
        """
        url = self.rest_api_url % (start_date, end_date)

        while True:
            response = requests.get(url, auth=(self.config['email'], self.config['password']))
            response.raise_for_status()
            response_json = json.loads(response.content)
            events = response_json['value']
            events = self.get_events_with_attendees(events)
            events = self.get_accepted_events(events)
            events = self.skip_ignored_events(events)
            # events = self.get_events_with_proper_dates(events)
            for event in events:
                yield {
                    'start_date': event['Start'],
                    'end_date': event['End'],
                    'title': event['Subject'].encode('utf8'),
                    'project_id': self.get_project_id(event['Body']['Content']),
                    'activity_id': self.get_activity_id(event['Body']['Content'])
                }
            url = response_json.get('@odata.nextLink', None)
            if not url:
                break
