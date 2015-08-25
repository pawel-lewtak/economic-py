import copy
import requests
import responses
import json
from economicpy.calendar_outlook import CalendarOutlook
from unittest import TestCase

config = [
    ('ignore_events', 'ignored,words,list'),
    ('project_id_pattern', '#economic[^0-9]+([0-9]+)'),
    ('activity_id_pattern', '#activity[^0-9]+([0-9]+)'),
    ('default_activity_id', 10),
    ('default_project_id', 20),
    ('email', 'email@example.com'),
    ('password', 'test')
]


class TestOutlookCalendar(TestCase):
    def test_ignore_event_returns_true(self):
        cal = CalendarOutlook(config)
        event = {
            'Subject': 'this contains ignored word'
        }
        self.assertTrue(cal.ignore_event(event))

    def test_ignore_event_returns_false(self):
        cal = CalendarOutlook(config)
        event = {
            'Subject': 'valid summary'
        }
        self.assertFalse(cal.ignore_event(event))

    def test_verify_dates_returns_false_for_different_start_and_end_dates(self):
        event = {
            'Subject': 'Valid summary',
            'Start': '1970-01-02',
            'End': '1970-01-01'
        }
        self.assertFalse(CalendarOutlook.verify_dates(event))

    def test_verify_dates_returns_true_for_valid_input(self):
        event = {
            'Subject': 'Valid summary',
            'Start': '1970-01-01',
            'End': '1970-01-01'
        }
        self.assertTrue(CalendarOutlook.verify_dates(event))

    def test_get_events_with_attendees_returns_empty_list_for_events_with_no_attendees(self):
        events = [
            {'Subject': 'Empty event with no attendees'},
            {'Subject': 'Empty event with no attendees'}
        ]
        calendar = CalendarOutlook(config)
        self.assertEquals(calendar.get_events_with_attendees(events), [])

    def test_get_events_with_attendees_returns_proper_response_with_attended_meetings_only(self):
        events = [
            {'Subject': 'Empty event with no attendees'}
        ]
        proper_event = {'Subject': 'Event with attendees', 'Attendees': True}
        events.append(proper_event)
        calendar = CalendarOutlook(config)
        self.assertEquals(calendar.get_events_with_attendees(events), [proper_event])

    def test_get_accepted_events_returns_empty_list_for_not_accepted_meeting(self):
        events = [
            {
                'Subject': 'Event with attendees',
                'Attendees': [
                    {'responseStatus': 'pending'}
                ],
                'ResponseStatus': {
                    'Response': 'NotResponded'
                }
            }
        ]
        self.assertEquals(CalendarOutlook.get_accepted_events(events), [])

    def test_get_accepted_events_returns_proper_response(self):
        events = [
            {
                'Subject': 'Event with attendees',
                'Attendees': [
                    {'responseStatus': 'pending'}
                ],
                'ResponseStatus': {
                    'Response': 'NotResponded'
                }
            }
        ]
        accepted_event = {
            'Subject': 'Accepted event with attendees',
            'Attendees': [
                {'responseStatus': 'accepted'}
            ],
            'ResponseStatus': {
                'Response': 'Accepted'
            }
        }
        events.append(accepted_event)
        self.assertEquals(CalendarOutlook.get_accepted_events(events), [accepted_event])

    def test_get_events_with_proper_dates(self):
        bad_event = {'Subject': 'Valid summary', 'Start': '1970-01-02', 'End': '1970-01-01'}
        good_event = {'Subject': 'Valid summary', 'Start': '1970-01-01', 'End': '1970-01-01'}
        events = [bad_event, good_event]
        cal = CalendarOutlook(config)
        self.assertEquals(cal.get_events_with_proper_dates(events), [good_event])

    def test_skip_ignored_events(self):
        ignored_event = {'Subject': 'this contains ignored word'}
        proper_event = {'Subject': 'Valid summary'}
        events = [ignored_event, proper_event]
        cal = CalendarOutlook(config)
        self.assertEquals(cal.skip_ignored_events(events), [proper_event])

    def test_get_project_id_returns_error_on_config_missing(self):
        config_copy = copy.copy(config)
        config_copy.append(('project_id_pattern', ''))
        cal = CalendarOutlook(config_copy)
        self.assertEquals(cal.get_project_id('description'), -1)

    def test_get_project_id_returns_default_project_id(self):
        cal = CalendarOutlook(config)
        self.assertEquals(cal.get_project_id('description'), 20)

    def test_get_project_id_returns_extracted_project_id(self):
        cal = CalendarOutlook(config)
        self.assertEquals(cal.get_project_id('#eConomic: 123'), 123)

    def test_get_activity_id_returns_error_on_config_missing(self):
        config_copy = copy.copy(config)
        config_copy.append(('activity_id_pattern', ''))
        cal = CalendarOutlook(config_copy)
        self.assertEquals(cal.get_activity_id('description'), -1)

    def test_get_activity_id_returns_default_activity_id(self):
        cal = CalendarOutlook(config)
        self.assertEquals(cal.get_activity_id('description'), 10)

    def test_get_activity_id_returns_exctracted_activity_id(self):
        cal = CalendarOutlook(config)
        self.assertEquals(cal.get_activity_id('#activitY: 234'), 234)

    @responses.activate
    def test_get_events_raises_exception_on_error(self):
        responses.add(responses.GET,
                      'https://outlook.office365.com/api/v1.0/me/calendarview?startDateTime=1970-01-01T00:00:00Z&endDateTime=1970-01-02T00:00:00Z',
                      body='', status=401,
                      content_type='text/html')
        cal = CalendarOutlook(config)
        events = cal.get_events(start_date='1970-01-01T00:00:00Z', end_date='1970-01-02T00:00:00Z')
        with self.assertRaises(requests.ConnectionError):
            events.next()

    @responses.activate
    def test_get_events_returns_proper_event_dict(self):
        response_body = {
            "value": [
                {
                    "Subject": "Outlook meeting",
                    "Body": {
                        "Content": "Meeting content"
                    },
                    "Start": "1970-01-01T07:30:00Z",
                    "End": "1970-01-01T07:45:00Z",
                    "ResponseStatus": {
                        "Response": "Accepted",
                        "Time": "1970-01-01T06:30:00.0000000Z"
                    },
                    "Attendees": [
                        {
                            "EmailAddress": {
                                "Address": "email@example.com",
                                "Name": "John Doe"
                            },
                            "Status": "Accepted"
                        }
                    ]
                }
            ]
        }
        responses.add(responses.GET,
                      'https://outlook.office365.com/api/v1.0/me/calendarview',
                      body=json.dumps(response_body), status=200,
                      content_type='application/json')
        cal = CalendarOutlook(config)
        events = cal.get_events(start_date='1970-01-01T00:00:00Z', end_date='1970-01-02T00:00:00Z')
        expected_event = {'activity_id': 10,
                          'end_date': u'1970-01-01T07:45:00Z',
                          'project_id': 20,
                          'start_date': u'1970-01-01T07:30:00Z',
                          'title': 'Outlook meeting'}
        self.assertEquals(events.next(), expected_event)

        # We expect just one event to be yielded and iteration to stop after that.
        with self.assertRaises(StopIteration):
            events.next()
