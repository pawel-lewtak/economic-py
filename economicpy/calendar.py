import re


class Calendar(object):
    """
    Base class that will serve to support different web based calendars.
    """

    def __init__(self, config):
        """
        Set configuration and init variables.

        :type config: list of tuples
        """
        self.config = {}
        for key, value in config:
            self.config[key] = value
        self.user_agent = 'economic-py/0.7'
        self.ignore_events = self.config['ignore_events'].lower().split(',')
        self.event_summary_field = ''
        self.event_attendees_field = ''

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
            if ignore_event and ignore_event in event[self.event_summary_field].lower():
                ignore = True

        return ignore

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
                print('SKIPPED (contains ignored phrase) - %s' % event[self.event_summary_field])

        return output

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

    def get_events_with_attendees(self, events):
        """
        From given list of events filter out events without attendees.

        :param events: list
        :return: list
        """
        output = []
        for event in events:
            if self.event_attendees_field in event:
                output.append(event)
            else:
                print("SKIPPED (no attendees) - %s" % (event[self.event_summary_field]))

        return output
