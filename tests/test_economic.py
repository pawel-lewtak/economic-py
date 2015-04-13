import responses
from unittest import TestCase
from economicpy.economic import Economic
from datetime import datetime

config = [('agreement', '123456'),
          ('username', 'USR'),
          ('password', 'password1'),
          ('default_project_id', '100'),
          ('append_title_for_activities', '10')]
date = datetime.now()


class TestEconomic(TestCase):
    @responses.activate
    def test_login_failed(self):
        responses.add(responses.POST, 'https://secure.e-conomic.com/secure/internal/login.asp',
                      body='<body onload="location.href=?open=&fejlbesked=1&loginfejltype=4;">', status=200,
                      content_type='text/html')
        self.assertRaises(Exception, Economic, config, date)

    @responses.activate
    def test_login_ok_no_medarbid(self):
        responses.add(responses.POST, 'https://secure.e-conomic.com/secure/internal/login.asp',
                      body='ok', status=200,
                      content_type='text/html')
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/subnav.asp',
                      body='no user id found in html', status=200)
        self.assertRaises(RuntimeError, Economic, config, date)

    @responses.activate
    def test_login_ok(self):
        responses.add(responses.POST, 'https://secure.e-conomic.com/secure/internal/login.asp',
                      body='ok', status=200,
                      content_type='text/html')
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/subnav.asp',
                      body='medarbid=10', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/generelt/dataedit.asp',
                      body='html task list', status=200)
        economic = Economic(config, date)
        self.assertEqual('10', economic.medarbid)
        self.assertEqual('html task list', economic.tasks_html)

    @responses.activate
    def test_get_description(self):
        responses.add(responses.POST, 'https://secure.e-conomic.com/secure/internal/login.asp',
                      body='ok', status=200,
                      content_type='text/html')
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/subnav.asp',
                      body='medarbid=10', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/generelt/dataedit.asp',
                      body='html task list', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/secure/applet/fbsearch/fbsearch.asp',
                      body='{"collection": [{"0": 1, "1": "project 1"},{"0": 2, "1": "project 2"},{"0": 3, "1": "project 3"}]}',
                      status=200)
        economic = Economic(config, date)
        economic.init_activities()
        self.assertRaises(RuntimeError, economic.get_description, 'Task Title', 10)

    @responses.activate
    def test_get_description_basic(self):
        responses.add(responses.POST, 'https://secure.e-conomic.com/secure/internal/login.asp',
                      body='ok', status=200,
                      content_type='text/html')
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/subnav.asp',
                      body='medarbid=10', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/generelt/dataedit.asp',
                      body='html task list', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/secure/applet/fbsearch/fbsearch.asp',
                      body='{"collection": [{"0": 1, "1": "project 1"},{"0": 2, "1": "project 2"},{"0": 3, "1": "project 3"},{"0": 20, "1": "Project Name"}]}',
                      status=200)
        economic = Economic(config, date)
        economic.init_activities()
        activity_description = economic.get_description('Task Title', 20)
        self.assertEqual('Project Name', activity_description)

    @responses.activate
    def test_get_description_appended(self):
        responses.add(responses.POST, 'https://secure.e-conomic.com/secure/internal/login.asp',
                      body='ok', status=200,
                      content_type='text/html')
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/subnav.asp',
                      body='medarbid=10', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/generelt/dataedit.asp',
                      body='html task list', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/secure/applet/fbsearch/fbsearch.asp',
                      body='{"collection": [{"0": 1, "1": "project 1"},{"0": 2, "1": "project 2"},{"0": 3, "1": "project 3"},{"0": 10, "1": "Project Name"}]}',
                      status=200)
        economic = Economic(config, date)
        economic.init_activities()
        activity_description = economic.get_description('Task Title', 10)
        self.assertEqual('Project Name - Task Title', activity_description)

    @responses.activate
    def test_convert_calendar_event_to_entry_basic(self):
        responses.add(responses.POST, 'https://secure.e-conomic.com/secure/internal/login.asp',
                      body='ok', status=200,
                      content_type='text/html')
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/subnav.asp',
                      body='medarbid=10', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/generelt/dataedit.asp',
                      body='html task list', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/secure/applet/fbsearch/fbsearch.asp',
                      body='{"collection": [{"0": 1, "1": "project 1"},{"0": 2, "1": "project 2"},{"0": 3, "1": "project 3"},{"0": 10, "1": "Project Name"}]}',
                      status=200)
        economic = Economic(config, date)
        event = {
            'start_date': date.isoformat(),
            'end_date': date.isoformat(),
            'project_id': 100,
            'title': 'Task Title',
            'activity_id': 10,
            'time_spent': '0'
        }
        expected_result = {
            'activity_id': 10,
            'date': date.isoformat()[:10],
            'project_id': 100,
            'task_description': 'Project Name - Task Title',
            'time_spent': '0,0'
        }
        entry = economic.convert_calendar_event_to_entry(event)
        self.assertEqual(entry, expected_result)

    @responses.activate
    def test_convert_calendar_event_to_with_wrong_date_format(self):
        responses.add(responses.POST, 'https://secure.e-conomic.com/secure/internal/login.asp',
                      body='ok', status=200,
                      content_type='text/html')
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/subnav.asp',
                      body='medarbid=10', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/generelt/dataedit.asp',
                      body='html task list', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/secure/applet/fbsearch/fbsearch.asp',
                      body='{"collection": [{"0": 1, "1": "project 1"},{"0": 2, "1": "project 2"},{"0": 3, "1": "project 3"},{"0": 10, "1": "Project Name"}]}',
                      status=200)
        economic = Economic(config, date)
        event = {
            'start_date': 'wrong date format',
            'end_date': date.isoformat()
        }
        entry = economic.convert_calendar_event_to_entry(event)
        self.assertEqual(None, entry)

    @responses.activate
    def test_add_time_entry_task_skipped(self):
        responses.add(responses.POST, 'https://secure.e-conomic.com/secure/internal/login.asp',
                      body='ok', status=200,
                      content_type='text/html')
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/subnav.asp',
                      body='medarbid=10', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/generelt/dataedit.asp',
                      body='duplicated entry', status=200)
        economic = Economic(config, date)
        entry = {
            'task_description': 'duplicated entry'
        }
        self.assertFalse(economic.add_time_entry(entry))

    @responses.activate
    def test_add_time_entry_task_dry_run_does_nothing(self):
        responses.add(responses.POST, 'https://secure.e-conomic.com/secure/internal/login.asp',
                      body='ok', status=200,
                      content_type='text/html')
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/subnav.asp',
                      body='medarbid=10', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/generelt/dataedit.asp',
                      body='html task list', status=200)
        economic = Economic(config, date)
        entry = {
            'task_description': 'Task description',
            'date': date.isoformat()[:10],
            'project_id': '10',
            'activity_id': '10',
            'time_spent': '0,0'
        }
        self.assertTrue(economic.add_time_entry(entry, dry_run=True))

    @responses.activate
    def test_add_time_entry_task_added_successfully(self):
        responses.add(responses.POST, 'https://secure.e-conomic.com/secure/internal/login.asp',
                      body='ok', status=200,
                      content_type='text/html')
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/subnav.asp',
                      body='medarbid=10', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/generelt/dataedit.asp',
                      body='html task list', status=200)
        responses.add(responses.POST, 'https://secure.e-conomic.com/secure/applet/df_doform.asp',
                      body='entry added', status=200)
        economic = Economic(config, date)
        entry = {
            'task_description': 'Task description',
            'date': date.isoformat()[:10],
            'project_id': '10',
            'activity_id': '10',
            'time_spent': '0,0'

        }
        self.assertTrue(economic.add_time_entry(entry))

    @responses.activate
    def test_add_time_entry_task_added_with_error(self):
        responses.add(responses.POST, 'https://secure.e-conomic.com/secure/internal/login.asp',
                      body='ok', status=200,
                      content_type='text/html')
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/subnav.asp',
                      body='medarbid=10', status=200)
        responses.add(responses.GET, 'https://secure.e-conomic.com/Secure/generelt/dataedit.asp',
                      body='html task list', status=200)
        responses.add(responses.POST, 'https://secure.e-conomic.com/secure/applet/df_doform.asp',
                      body='{"errorMessage": "something went wrong"}', status=200)
        economic = Economic(config, date)
        entry = {
            'task_description': 'Task description',
            'date': date.isoformat()[:10],
            'project_id': '10',
            'activity_id': '10',
            'time_spent': '0,0'

        }
        self.assertFalse(economic.add_time_entry(entry))


