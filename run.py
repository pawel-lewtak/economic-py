#!/usr/bin/env python
from __future__ import print_function
import ConfigParser
import datetime
import os
from economicpy.gcal import Calendar
from economicpy.jira import Jira
from economicpy.economic import Economic


try:
    src_path = os.path.abspath(os.path.dirname(__file__))
    configFile = os.path.join(src_path, 'config.ini')
    if not os.path.isfile(configFile):
        raise Exception('Configuration file config.ini not found.')
    config = ConfigParser.ConfigParser()
    config.read(configFile)

    economic = Economic(config.items('Economic'))

    # Add entries from Google Calendar.
    try:
        calendar = Calendar(config.get('Google', 'client_id'), config.get('Google', 'client_secret'),
                            config.get('Google', 'ignore_events'), src_path)
        today = datetime.datetime.now().isoformat()[:10] + "T00:00:00Z"
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()[:10] + "T00:00:00Z"
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
