from __future__ import print_function
import re
import json
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
        try:
            if response.status_code != 200:
                raise Exception('ERROR: login to JIRA failed (check credentials)')

            return json.loads(response.text)
        except ValueError:
            raise Exception("ERROR - Couldn't fetch JIRA tasks.")

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
                    'task_description': '%s %s' % (issue['key'], issue['fields']['summary']), 'time_spent': '0'
                }
                yield task

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
