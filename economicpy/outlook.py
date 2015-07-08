from __future__ import print_function
import requests
import re
import json


class OutlookCalendar(object):
    """
    Class related to communication with Google Calendar using API V3.

    :param config: list
    """

    def __init__(self, config):
        """
        Set configuration and init variables.

        :type config: list of tuples
        """
        self.config = {}
        for key, value in config:
            self.config[key] = value
        self.ignore_events = self.config['ignore_events'].lower().split(',')
        self.rest_api_url = 'https://outlook.office365.com/api/v1.0/me/calendarview?startDateTime=%s&endDateTime=%s'
        if self.config.get('mock_enabled', False):
            return

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
            if ignore_event and ignore_event in event['Subject'].lower():
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
        if event['Start'][:10] != event['End'][:10]:
            print("SKIPPED (event start and end days are different) - %s" % (event['Subject']))
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
            if 'Attendees' in event:
                output.append(event)
            else:
                print("SKIPPED (no attendees) - %s" % (event['Subject']))

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
                print('SKIPPED (contains ignored phrase) - %s' % event['Subject'])

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
