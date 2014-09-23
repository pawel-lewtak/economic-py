import gdata.calendar.client
import gdata.client


class Calendar:
    def __init__(self, username, password, ignore_events):
        try:
            self.username = username[:username.find('@') + 1]
            self.cal_client = gdata.calendar.client.CalendarClient(source='Google-Calendar_Python_Sample-1.0')
            self.cal_client.ClientLogin(username, password, self.cal_client.source)
            self.ignore_events = ignore_events
        except gdata.client.BadAuthentication:
            raise Exception('ERROR: login to Google failed (check credentials)')

    def get_events(self, start_date, end_date):
        """
        Get events from calendar between given dates.
        """
        query = gdata.calendar.client.CalendarEventQuery(start_min=start_date, start_max=end_date, singleevents="true")
        feed = self.cal_client.GetCalendarEventFeed(q=query)
        for i, an_event in zip(range(len(feed.entry)), feed.entry):
            for who in [x for x in an_event.who if self.username in x.email]:
                if who.attendee_status is not None and "declined" not in who.attendee_status.value:
                    for an_when in [x for x in an_event.when if an_event.title.text not in self.ignore_events]:
                        yield {
                            'start_date': an_when.start,
                            'end_date': an_when.end,
                            'title': an_event.title.text
                        }
