from __future__ import print_function
import re
import requests
import datetime


class Jira(object):

    """
    Class responsible for communication with JIRA.

    :param config: list
    """

    def __init__(self, config):
        """
        Save configuration options.

        :param config: list
        """
        self.config = {}
        for item in config:
            self.config[item[0]] = item[1]

        self.auth_data = (self.config['username'], self.config['password'])

    def make_request(self, uri):
        """
        Generic method for making requests to JIRA API.

        :type uri: str
        :param uri:
        """
        response = requests.get(self.config['api_url'] + uri, auth=self.auth_data)
        response.raise_for_status()

        return response.json()

    def get_tasks(self):
        """Generator returning all tasks assigned to current user that match filter specified in configuration."""
        tasks = self.make_request(
            'search?jql=' + self.config['search_query'] + '&fields=*all,-comment'
        )

        for issue in tasks['issues']:
            project_id = self.get_project_id(issue['fields'])
            if not project_id:
                print('ERROR - task %s is missing economic project ID' % (issue['key']))
                continue

            task = {
                'date': datetime.datetime.now().isoformat()[:10],
                'project_id': project_id,
                'activity_id': self.get_activity_id(),
                'task_description': '%s %s' % (issue['key'], issue['fields']['summary']),
                'time_spent': str(self.get_hours(issue['key'])).replace('.', ',')
            }

            yield task

    def get_hours(self, issue):
        """
        Get sum of hours registered in JIRA worklog or return 0 (zero) if worklog is not used.

        :param issue:
        :return float
        """
        hours = 0.0

        now = str(datetime.datetime.now())[:10]
        for worklog in self.get_worklog(issue):
            if worklog['author']['name'] == self.config['username'] and worklog['started'].startswith(now):
                hours += worklog['timeSpentSeconds']

        return hours / 3600

    def get_worklog(self, issue_id):
        """
        Make separate API call for given issue's worklog and return it.

        :param issue_id:
        :type issue_id: str
        :return list
        """
        return self.make_request('issue/%s/worklog' % issue_id)['worklogs']

    def get_project_id(self, fields):
        """
        Get numeric E-conomic ID from JIRA task.

        Economic field might be either select box or input field.
        Value might be either numeric or contain number and project's name.

        :param fields:
        :type fields: dict
        :return bool|int
        """
        for field in self.config['economic_field'].split(','):
            if field in fields:
                project_id = self.extract_project_id(fields[field])
                if project_id:
                    return project_id

        return False

    @staticmethod
    def extract_project_id(field):
        """
        Extract project ID from given string.

        :param field: str
        :return: int|None
        """
        if type(field) is dict:
            project_id = str(field['value'])
        else:
            project_id = str(field)

        search = re.search(r'^\d+', project_id)
        if search:
            return int(search.group())

        return None

    def get_activity_id(self):
        """
        Return activity ID.

        :return bool|int
        """
        return self.config.get('default_activity_id', False)
