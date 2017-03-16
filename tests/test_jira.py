# -*- coding: utf-8 -*-
import pytest
import requests
import responses
import copy
import datetime
import re
from economicpy.jira import Jira
from unittest import TestCase

CONFIG = [
    ('username', 'sample_username'),
    ('password', 'sample_password'),
    ('api_url', 'http://jira.example.com/'),
]


class TestJira(TestCase):
    def test_jira_init_fails_with_empty_config(self):
        with pytest.raises(KeyError):
            Jira([])

    def test_jira_init_ok_with_proper_config(self):
        jira = Jira(CONFIG)
        assert type(jira) == Jira

    @responses.activate
    def test_jira_auth_fails_for_invalid_method(self):
        responses.add(responses.GET, 'http://jira.example.com/invalid_method',
                      body='{"error": "not found"}', status=404,
                      content_type='application/json')
        jira = Jira(CONFIG)
        with pytest.raises(requests.HTTPError):
            jira.make_request('invalid_method')

    @responses.activate
    def test_jira_auth_ok_for_basic_request(self):
        responses.add(responses.GET, 'http://jira.example.com/search',
                      body='{"startAt":0,"maxResults":50,"total":0,"issues":[]}', status=200,
                      content_type='application/json')
        jira = Jira(CONFIG)
        response = jira.make_request('search')
        assert 0 == response['total']

    def test_default_activity_as_defined_in_config(self):
        config = copy.copy(CONFIG)
        config.append(('default_activity_id', 1))
        jira = Jira(config)
        assert 1 == jira.get_activity_id()

    def test_default_activity_false_when_not_defined(self):
        jira = Jira(CONFIG)
        assert jira.get_activity_id() is False

    @responses.activate
    def test_jira_returns_worklog(self):
        responses.add(responses.GET, 'http://jira.example.com/issue/TEST-1/worklog',
                      body='{"startAt":0,"maxResults":50,"total":1,"worklogs":["worklog"]}', status=200,
                      content_type='application/json')
        jira = Jira(CONFIG)
        response = jira.get_worklog('TEST-1')
        assert ["worklog"] == response

    def test_project_id_as_false_when_no_economic_field_defined(self):
        config = copy.copy(CONFIG)
        config.append(('economic_field', ''))
        jira = Jira(config)
        assert jira.get_project_id({}) is False

    def test_project_id_not_in_defined_field(self):
        config = copy.copy(CONFIG)
        config.append(('economic_field', 'customfield'))
        jira = Jira(config)
        assert jira.get_project_id({}) is False

    def test_project_id_as_dict(self):
        config = copy.copy(CONFIG)
        config.append(('economic_field', 'custom_field'))
        jira = Jira(config)
        fields = {'id': 1, 'custom_field': {'value': 123}, 'other_field': 234}
        assert 123 == jira.get_project_id(fields)

    def test_project_id_as_value(self):
        config = copy.copy(CONFIG)
        config.append(('economic_field', 'custom_field'))
        jira = Jira(config)
        fields = {'id': 1, 'custom_field': 123, 'other_field': 234}
        assert 123 == jira.get_project_id(fields)

    def test_project_id_as_value_multiple_fields_defined(self):
        config = copy.copy(CONFIG)
        config.append(('economic_field', 'custom_field,second_field'))
        jira = Jira(config)
        fields = {'id': 1, 'custom_field': 123, 'other_field': 234}
        assert 123 == jira.get_project_id(fields)

    def test_project_id_as_value_part_of_string(self):
        config = copy.copy(CONFIG)
        config.append(('economic_field', 'custom_field'))
        jira = Jira(config)
        fields = {'id': 1, 'custom_field': '123 project name', 'other_field': 234}
        assert 123 == jira.get_project_id(fields)

    def test_project_id_does_not_contain_number_value(self):
        config = copy.copy(CONFIG)
        config.append(('economic_field', 'custom_field'))
        jira = Jira(config)
        fields = {'id': 1, 'custom_field': 'project name', 'other_field': 234}
        assert jira.get_project_id(fields) is False

    def test_project_id_contains_non_ascii_character(self):
        config = copy.copy(CONFIG)
        config.append(('economic_field', 'custom_field'))
        jira = Jira(config)
        fields = {'id': 1, 'custom_field': '123 — project name', 'other_field': 234}
        assert jira.get_project_id(fields) == 123

    @responses.activate
    def test_hours_without_worklog(self):
        responses.add(responses.GET, 'http://jira.example.com/issue/TEST-1/worklog',
                      body='{"startAt":0,"maxResults":50,"total":1,"worklogs":[]}', status=200,
                      content_type='application/json')
        config = copy.copy(CONFIG)
        jira = Jira(config)
        assert 0.0 == jira.get_hours('TEST-1')

    @responses.activate
    def test_hours_with_worklog(self):
        now = datetime.datetime.now()
        responses.add(responses.GET, 'http://jira.example.com/issue/TEST-1/worklog',
                      body='{"startAt":0,"maxResults":50,"total":1,"worklogs":[{"author":{"name":"sample_username"},"timeSpentSeconds":1800,"started":"%s"},{"author":{"name":"other_user"},"timeSpentSeconds":3600,"started":"%s"}]}' % (now, now),
                      status=200,
                      content_type='application/json')
        config = copy.copy(CONFIG)
        jira = Jira(config)
        assert 0.5 == jira.get_hours('TEST-1')

    @responses.activate
    def test_get_tasks_empty_result(self):
        config = copy.copy(CONFIG)
        config.append(('search_query', 'test'))
        config.append(('economic_field', 'customfield_economic'))
        config.append(('default_activity_id', '100'))

        url_re = re.compile(r'http://jira\.example\.com/search\?jql(.)+')
        responses.add(responses.GET, url_re,
                      body='{"startAt": 0,"maxResults": 50,"total": 0,"issues": []}',
                      status=200,
                      content_type='application/json')
        responses.add(responses.GET, 'http://jira.example.com/issue/TEST-1/worklog',
                      body='{"startAt":0,"maxResults":50,"total":1,"worklogs":[]}', status=200,
                      content_type='application/json')
        jira = Jira(config)
        tasks = jira.get_tasks()
        assert False == next(tasks, False)

    @responses.activate
    def test_get_one_task(self):
        config = copy.copy(CONFIG)
        config.append(('search_query', 'test'))
        config.append(('economic_field', 'customfield_economic'))
        config.append(('default_activity_id', '100'))

        url_re = re.compile(r'http://jira\.example\.com/search\?jql(.)+')
        responses.add(responses.GET, url_re,
                      body='{"startAt": 0,"maxResults": 50,"total": 1,"issues": [{"key": "TEST-1","fields": {"summary": "Task summary","customfield_economic": "200 project X"}}]}',
                      status=200,
                      content_type='application/json')
        responses.add(responses.GET, 'http://jira.example.com/issue/TEST-1/worklog',
                      body='{"startAt":0,"maxResults":50,"total":1,"worklogs":[]}', status=200,
                      content_type='application/json')
        jira = Jira(config)
        task = next(jira.get_tasks())
        assert '100' == task['activity_id']
        assert datetime.datetime.now().isoformat()[:10] == task['date']
        assert 200 == task['project_id']
        assert 'TEST-1 Task summary' == task['task_description']
        assert '0,0' == task['time_spent']

    @responses.activate
    def test_get_task_without_economic_id(self):
        config = copy.copy(CONFIG)
        config.append(('search_query', 'test'))
        config.append(('economic_field', 'customfield_economic'))
        config.append(('default_activity_id', '100'))

        url_re = re.compile(r'http://jira\.example\.com/search\?jql(.)+')
        responses.add(responses.GET, url_re,
                      body='{"startAt": 0,"maxResults": 50,"total": 1,"issues": [{"key": "TEST-2","fields": {"summary": "Task summary","customfield": "value"}}]}',
                      status=200,
                      content_type='application/json')
        responses.add(responses.GET, 'http://jira.example.com/issue/TEST-2/worklog',
                      body='{"startAt":0,"maxResults":50,"total":1,"worklogs":[]}', status=200,
                      content_type='application/json')
        jira = Jira(config)
        tasks = jira.get_tasks()
        assert next(tasks, False) is False
