#!/usr/bin/env python
import datetime
import ConfigParser
import os
from gcal import Calendar
from jira import Jira
from economic import Economic

try:
    configFile = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini')
    if not os.path.isfile(configFile):
        raise Exception('Configuration file config.ini not found.')
    config = ConfigParser.ConfigParser()
    config.read(configFile)

    economic = Economic(config.items('Economic'))

    # Add entries from Google Calendar.
    try:
        calendar = Calendar(config.get('Google', 'username'), config.get('Google', 'password'),
                            config.get('Google', 'ignore_events'))
        today = datetime.datetime.now().isoformat()[:10]
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()[:10]
        for event in calendar.get_events(today, tomorrow):
            entry = economic.convert_calendar_event_to_entry(event)
            if entry:
                economic.add_time_entry(entry)
    except Exception as e:
        print(e.message)

    # Add entries from JIRA.
    try:
        jira = Jira(config.items('Jira'))
        for task in jira.get_tasks():
            if task:
                task = economic.convert_jira_task_to_entry(task)
                economic.add_time_entry(task)
    except Exception as e:
        print(e.message)

except Exception as e:
    print(e.message)
