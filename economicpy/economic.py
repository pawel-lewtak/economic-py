from __future__ import print_function
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup


class Economic(object):
    def __init__(self, config):
        self.session = requests.session()
        self.tasks_html = ""
        self.medarbid = ""
        self.activities = {}
        self.config = {}
        for item in config:
            self.config[item[0]] = item[1]

        self.login()

    def login(self):
        """
        Login to e-conomic service, parse page looking for internal user ID
        and fetch already registered tasks.

        :raise Exception: raised in case of invalid credentials
        """
        response = self.session.post('https://secure.e-conomic.com/secure/internal/login.asp',
                                     {
                                         'aftalenr': self.config['agreement'],
                                         'brugernavn': self.config['username'],
                                         'password': self.config['password'],
                                     },
                                     allow_redirects=True)
        if 'login.e-conomic.com' in response.content:
            raise Exception("ERROR: login to economic failed (check credentials)")

        self.init_medarbid()
        self.init_tasks()

    def init_activities(self):
        """
        Get list of available activities from e-conomic and cache it for future use.
        """
        url = "https://secure.e-conomic.com/secure/applet/fbsearch/fbsearch.asp?kar=10&id=%s&maxResultLength=1000"
        response = self.session.get(url % self.config['default_project_id'])
        soup = BeautifulSoup(response.content)
        table = soup.find("table")

        for row in table.find_all("tr", attrs={"class": "row"}):
            data = [td.get_text() for td in row.find_all("td")]
            self.activities[int(data[0])] = data[1]

    def add_time_entry(self, entry, dry_run=False):
        """
        Method used to save given dict entry as Economic entry.
        Result is based on html response.

        :param entry: dictionary with data to be added
        :param dry_run: whether to really insert data or just simulate it
        :type entry: dict
        :type dry_run: bool
        :return bool
        """
        entry['task_description'] = entry['task_description'].decode().encode('utf-8')
        if entry['task_description'][:20] in self.tasks_html:
            print("SKIPPED - %s" % (entry['task_description']))
            return False

        if dry_run:
            print("OK - time entry will be added: %s" % (entry['task_description']))
            return True

        url = "https://secure.e-conomic.com/secure/applet/df_doform.asp?form=80&medarbid={MEDARBID}&theaction=post"
        url = url.replace('{MEDARBID}', self.medarbid)
        response = self.session.post(url,
                                     {
                                         'cs1': str(entry['date']),
                                         'cs2': str(entry['project_id']),
                                         'cs3': str(entry['activity_id']),
                                         'cs6': str(entry['task_description']),
                                         'cs7': str(entry['time_spent']),
                                         'cs10': "False",
                                         'cs11': "False",
                                         'cs4': None
                                     })
        if response.content.find("../generelt/dataedit.asp"):
            print("OK - time entry added: %s" % (entry['task_description']))
            return True

        print("ERROR - time entry not added. Entry: %s; Response: %s" % (entry['task_description'], response.content))
        return False

    def convert_calendar_event_to_entry(self, event):
        """
        Converts Google Calendar event object to a dict object that will later be inserted to Economic.
        :type event: dict
        :param event:
        """
        if not self.activities:
            self.init_activities()

        try:
            start_date = datetime.strptime(event['start_date'][:19], "%Y-%m-%dT%H:%M:%S")
            end_date = datetime.strptime(event['end_date'][:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None

        time_spent = (end_date - start_date).total_seconds() / 3600

        entry = {
            'date': str(start_date.isoformat()[:-9]),
            'project_id': event.get('project_id', False) or self.config['default_project_id'],
            'activity_id': event.get('activity_id'),
            'task_description': self.get_description(event['title'], event.get('activity_id')),
            'time_spent': str(time_spent).replace('.', ',')
        }

        return entry

    def init_tasks(self):
        """
        This method fetches list of currently entered tasks and saves it as HTML (without parsing).
        It will be later used to avoid entering duplicated entries.
        """
        url = 'https://secure.e-conomic.com/Secure/generelt/dataedit.asp?' \
              'form=80&projektleder=&medarbid=' + self.medarbid + '&mode=dag&dato='
        today = datetime.now()
        date = "%s-%s-%s" % (today.day, today.month, today.year)
        response = self.session.get(url + date)
        self.tasks_html = response.content

    def init_medarbid(self):
        """
        In order to make Economic work we need user ID. Even though we pass User ID in login form,
        Economic is internally using another user ID called "medarbid" which indicates specific
        user within given agreement number.

        Fun fact: changing this ID allows you to add entries for another user without need for his credentials.
        """
        url = "https://secure.e-conomic.com/Secure/subnav.asp?subnum=10"
        response = self.session.get(url)

        medarbid = re.search(r'medarbid=(\d+)', response.content)
        if medarbid:
            self.medarbid = medarbid.groups()[0]
        else:
            raise RuntimeError('There is problem when trying to determine economic internal user id.')

    def get_description(self, title, activity_id):
        """
        For defined activity IDs title should be concatenation of default
        activity description and calendar event title. As fallback
        just default activity description is returned.

        :param title:
        :param activity_id:
        :type title: str
        :type activity_id: int
        :return str
        """
        activity_ids = []
        if self.config.get('append_title_for_activities'):
            activity_ids = map(int, self.config.get('append_title_for_activities').split(','))

        default_activity = self.activities.get(int(activity_id), False)

        if default_activity is False:
            message = 'ERROR - No activity found with ID = %s' % str(activity_id)
            raise Exception(message)

        if int(activity_id) in activity_ids:
            return "%s - %s" % (default_activity, title)

        return default_activity