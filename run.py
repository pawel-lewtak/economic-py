#!/usr/bin/env python
from __future__ import print_function
import ConfigParser
import datetime
import os
import click
import sys
import requests.packages.urllib3
from economicpy.calendar_google import CalendarGoogle
from economicpy.jira import Jira
from economicpy.economic import Economic
from economicpy.config_check import ConfigCheck
from economicpy.calendar_outlook import CalendarOutlook

requests.packages.urllib3.disable_warnings()


@click.command()
@click.option('--dry-run', is_flag=True, default=False, help='Simulated run without creating new entries.')
@click.option('--date', default=None, help='Date in format YYYY-MM-DD for which data should be used.')
def run(dry_run=False, date=None):
    """
    Main function to be run in order to export data to e-conomic.

    :param dry_run: Simulated run without creating new entries in e-conomic
    :param date: date in format YYYY-MM-DD
    """
    try:
        skip_jira = False
        if date:
            date = datetime.datetime.strptime(str(date), "%Y-%m-%d")
            # Can't import tasks from Jira for given day yet. See issue #16
            skip_jira = True
        else:
            date = datetime.datetime.now()
    except ValueError:
        sys.exit("Incorrect date format used. Expected: YYYY-MM-DD")

    if dry_run:
        print("This is just dry run, no changes will be made.")
    print("Running export for %s:" % date.isoformat()[:10])

    src_path = os.path.abspath(os.path.dirname(__file__))
    config = get_configuration(src_path)
    economic = Economic(config.items('Economic'), date)

    # Get entries from provided calendar.
    calendar = get_calendar_provider(config, src_path)
    add_calendar_entries(calendar, dry_run, economic, date)

    # Add entries from JIRA.
    if not skip_jira:
        add_jira_entries(config, date, dry_run, economic)


def add_calendar_entries(calendar, dry_run, economic, date):
    """
    Add Calendar meetings as time entries to E-conomic

    :param calendar:
    :param dry_run:
    :param economic:
    :param date:
    :return:
    """
    today = date.isoformat()[:10] + "T00:00:00Z"
    tomorrow = (date + datetime.timedelta(days=1)).isoformat()[:10] + "T00:00:00Z"
    for event in calendar.get_events(today, tomorrow):
        try:
            entry = economic.convert_calendar_event_to_entry(event)
            if entry:
                economic.add_time_entry(entry, dry_run)
        except UnicodeDecodeError as e:
            print(e)


def add_jira_entries(config, date, dry_run, economic):
    """
    Add JIRA tasks as time entries to E-conomic

    :param config:
    :param date:
    :param dry_run:
    :param economic:
    :return:
    """
    if date is not None:
        jira = Jira(config.items('Jira'))
        for task in jira.get_tasks():
            if task:
                economic.add_time_entry(task, dry_run)


def get_configuration(src_path):
    """
    Return configuration as list of tuples read from config file.

    :param src_path: path to current directory
    :return: list of tuples
    """
    config_file = os.path.join(src_path, 'config.ini')
    config_check = ConfigCheck(config_file + '.dist', config_file)
    if not config_check.check_sections(['Google', 'Economic', 'Jira', 'Office365']):
        sys.exit(1)
    config = ConfigParser.ConfigParser()
    config.read(config_file)

    return config


def get_calendar_provider(config, src_path):
    """
    Return calendar object based on provider set in config file.

    :param config: list of tuples
    :param src_path: path to current directory
    :return: Calendar|OutlookCalendar
    """
    economic_config = dict(config.items('Economic'))
    if 'Google' == economic_config['calendar_provider']:
        calendar = CalendarGoogle(config.items('Google'), src_path)
    elif 'Office365' == economic_config['calendar_provider']:
        calendar = CalendarOutlook(config.items('Office365'))
    else:
        print("Unsupported calendar provider")
        sys.exit(1)

    return calendar


if __name__ == '__main__':
    run()
