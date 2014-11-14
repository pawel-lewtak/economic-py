from __future__ import print_function
import re
import requests
import datetime


class Jira(object):
    def __init__(self, config):
        self.config = {}
        for item in config:
            self.config[item[0]] = item[1]

        self.auth_data = (self.config['username'], self.config['password'])

    def make_request(self, uri):
        """
        Generic method for making requests to JIRA API.
        """
        response = requests.get(self.config['api_url'] + uri, auth=self.auth_data)
        response.raise_for_status()

        return response.json()

    def get_tasks(self):
        """
        Generator returning all tasks assigned to current user that match filter specified in configuration
        """
        tasks = self.make_request(
            'search?jql=' + self.config['search_query'] + '&fields=*all,-comment'
        )
        if not tasks:
            return

        for issue in tasks['issues']:
            if self.config['economic_field'] not in issue['fields']:
                print('ERROR - task %s is missing economic project ID' % (issue['key']))
                yield None
            else:
                task = {
                    'date': datetime.datetime.now().isoformat()[:10],
                    'project_id': self.get_project_id(issue['fields'][self.config['economic_field']]),
                    'task_description': '%s %s' % (issue['key'], issue['fields']['summary']),
                    'time_spent': str(self.get_hours(issue['key'])).replace('.', ',')
                }

                yield task

    def get_hours(self, issue):
        hours = 0.0
        if not int(self.config['use_worklog']):
            return hours

        now = str(datetime.datetime.now())[:10]
        for worklog in self.get_worklog(issue):
            if worklog['author']['name'] == self.config['username'] and worklog['started'].startswith(now):
                hours += worklog['timeSpentSeconds']

        return hours / 3600

    def get_worklog(self, issue_id):
        return self.make_request('issue/%s/worklog' % issue_id)

    def get_project_id(self, economic_field):
        """
        Economic field might be either select box or input field.
        Value might be either numeric or contain number and project's name.

        :param economic_field:
        :return: :rtype:
        """
        if type(economic_field) is dict:
            project_id = str(economic_field['value'])
        else:
            project_id = str(economic_field)

        return int(re.search(r'^\d+', project_id).group())
