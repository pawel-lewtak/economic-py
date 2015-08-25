import copy
from economicpy.calendar_google import CalendarGoogle
from unittest import TestCase

config = [
    ('ignore_events', 'ignored,words,list'),
    ('project_id_pattern', '#economic[^0-9]+([0-9]+)'),
    ('activity_id_pattern', '#activity[^0-9]+([0-9]+)'),
    ('default_activity_id', 10),
    ('default_project_id', 20),
    ('mock_enabled', True)
]


class TestCalendar(TestCase):
    def test_ignore_event_returns_true(self):
        cal = CalendarGoogle(config, '')
        event = {
            'summary': 'this contains ignored word'
        }
        self.assertTrue(cal.ignore_event(event))

    def test_ignore_event_returns_false(self):
        cal = CalendarGoogle(config, '')
        event = {
            'summary': 'valid summary'
        }
        self.assertFalse(cal.ignore_event(event))

    def test_verify_dates_returns_false_for_missing_start_date(self):
        event = {
            'summary': 'Valid summary',
            'start': {},
            'end': {
                'dateTime': ''
            }
        }
        self.assertFalse(CalendarGoogle.verify_dates(event))

    def test_verify_dates_returns_false_for_missing_end_date(self):
        event = {
            'summary': 'Valid summary',
            'start': {
                'dateTime': ''
            },
            'end': {}
        }
        self.assertFalse(CalendarGoogle.verify_dates(event))

    def test_verify_dates_returns_false_for_different_start_and_end_dates(self):
        event = {
            'summary': 'Valid summary',
            'start': {
                'dateTime': '1970-01-02'
            },
            'end': {
                'dateTime': '1970-01-01'
            }
        }
        self.assertFalse(CalendarGoogle.verify_dates(event))

    def test_verify_dates_returns_true_for_valid_input(self):
        event = {
            'summary': 'Valid summary',
            'start': {
                'dateTime': '1970-01-01'
            },
            'end': {
                'dateTime': '1970-01-01'
            }
        }
        self.assertTrue(CalendarGoogle.verify_dates(event))

    def test_get_events_with_attendees_returns_empty_list_for_events_with_no_attendees(self):
        events = [
            {'summary': 'Empty event with no attendees'},
            {'summary': 'Empty event with no attendees'}
        ]
        calendar_google = CalendarGoogle(config, '')
        self.assertEquals(calendar_google.get_events_with_attendees(events), [])

    def test_get_events_with_attendees_returns_proper_response_with_attended_meetings_only(self):
        events = [
            {'summary': 'Empty event with no attendees'}
        ]
        proper_event = {'summary': 'Event with attendees', 'attendees': True}
        events.append(proper_event)
        calendar_google = CalendarGoogle(config, '')
        self.assertEquals(calendar_google.get_events_with_attendees(events), [proper_event])

    def test_get_accepted_events_returns_empty_list_for_not_accepted_meeting(self):
        events = [
            {
                'summary': 'Event with attendees',
                'attendees': [
                    {'responseStatus': 'pending', 'self': True}
                ]
            }
        ]
        self.assertEquals(CalendarGoogle.get_accepted_events(events), [])

    def test_get_accepted_events_returns_proper_response(self):
        events = [
            {
                'summary': 'Event with attendees',
                'attendees': [
                    {'responseStatus': 'pending', 'self': True}
                ]
            }
        ]
        accepted_event = {
            'summary': 'Accepted event with attendees',
            'attendees': [
                {'responseStatus': 'accepted', 'self': True}
            ]
        }
        events.append(accepted_event)
        self.assertEquals(CalendarGoogle.get_accepted_events(events), [accepted_event])

    def test_get_events_with_proper_dates(self):
        bad_event = {'summary': 'Valid summary', 'start': {'dateTime': '1970-01-02'}, 'end': {'dateTime': '1970-01-01'}}
        good_event = {'summary': 'Valid summary', 'start': {'dateTime': '1970-01-01'}, 'end': {'dateTime': '1970-01-01'}}
        events = [bad_event, good_event]
        cal = CalendarGoogle(config, '')
        self.assertEquals(cal.get_events_with_proper_dates(events), [good_event])

    def test_skip_ignored_events(self):
        ignored_event = {'summary': 'this contains ignored word'}
        proper_event = {'summary': 'Valid summary'}
        events = [ignored_event, proper_event]
        cal = CalendarGoogle(config, '')
        self.assertEquals(cal.skip_ignored_events(events), [proper_event])

    def test_get_project_id_returns_error_on_config_missing(self):
        config_copy = copy.copy(config)
        config_copy.append(('project_id_pattern', ''))
        cal = CalendarGoogle(config_copy, '')
        self.assertEquals(cal.get_project_id('description'), -1)

    def test_get_project_id_returns_default_project_id(self):
        cal = CalendarGoogle(config, '')
        self.assertEquals(cal.get_project_id('description'), 20)

    def test_get_project_id_returns_extracted_project_id(self):
        cal = CalendarGoogle(config, '')
        self.assertEquals(cal.get_project_id('#eConomic: 123'), 123)

    def test_get_activity_id_returns_error_on_config_missing(self):
        config_copy = copy.copy(config)
        config_copy.append(('activity_id_pattern', ''))
        cal = CalendarGoogle(config_copy, '')
        self.assertEquals(cal.get_activity_id('description'), -1)

    def test_get_activity_id_returns_default_activity_id(self):
        cal = CalendarGoogle(config, '')
        self.assertEquals(cal.get_activity_id('description'), 10)

    def test_get_activity_id_returns_exctracted_activity_id(self):
        cal = CalendarGoogle(config, '')
        self.assertEquals(cal.get_activity_id('#activitY: 234'), 234)
