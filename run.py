#!/usr/bin/env python
from __future__ import print_function
import ConfigParser
import datetime
import os
import click
import sys
from economicpy.gcal import Calendar
from economicpy.jira import Jira
from economicpy.economic import Economic
from economicpy.configcheck import ConfigCheck


@click.command()
@click.option('--dry-run', is_flag=True, default=False, help='Simulated run without creating new entries.')
@click.option('--date', default=None, help='Date in format YYYY-MM-DD for which data should be used.')
def run(dry_run, date):
    try:
        exclude_jira = False
        if date:
            date = datetime.datetime.strptime(str(date), "%Y-%m-%d")
            exclude_jira = True
        else:
            date = datetime.datetime.now()
        today = date.isoformat()[:10] + "T00:00:00Z"
        tomorrow = (date + datetime.timedelta(days=1)).isoformat()[:10] + "T00:00:00Z"
        print ("Running export for %s:" % date.isoformat()[:10])
    except ValueError:
        print('Invalid date provided. Use YYYY-MM-DD format.')
        sys.exit(1)

    try:
        src_path = os.path.abspath(os.path.dirname(__file__))
        config_file = os.path.join(src_path, 'config.ini')
        config_check = ConfigCheck(config_file + '.dist', config_file)
        if not config_check.check_sections(['Google', 'Economic', 'Jira']):
            sys.exit(1)
        config = ConfigParser.ConfigParser()
        config.read(config_file)

        economic = Economic(config.items('Economic'), date)
    except Exception as e:
        print(e.message)

    # Add entries from Google Calendar.
    try:
        calendar = Calendar(config.items('Google'), src_path)
        for event in calendar.get_events(today, tomorrow):
            entry = economic.convert_calendar_event_to_entry(event)
            if entry:
                economic.add_time_entry(entry, dry_run)
    except Exception as e:
        print(e.message)

    # Add entries from JIRA.
    try:
        if not exclude_jira:
            jira = Jira(config.items('Jira'))
            for task in jira.get_tasks():
                if task:
                    economic.add_time_entry(task, dry_run)
    except Exception as e:
        print(e.message)


if __name__ == '__main__':
    run()