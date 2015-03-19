economic-py
===========
[![Build status](https://travis-ci.org/pawel-lewtak/economic-py.png)](https://travis-ci.org/pawel-lewtak/economic-py) [![Code Health](https://landscape.io/github/pawel-lewtak/economic-py/master/landscape.svg)](https://landscape.io/github/pawel-lewtak/economic-py/master) [![Requirements Status](https://requires.io/github/pawel-lewtak/economic-py/requirements.svg?branch=master)](https://requires.io/github/pawel-lewtak/economic-py/requirements/?branch=master) [![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/pawel-lewtak/economic-py/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/pawel-lewtak/economic-py/?branch=master) [![Coverage Status](https://coveralls.io/repos/pawel-lewtak/economic-py/badge.svg)](https://coveralls.io/r/pawel-lewtak/economic-py)  

# About
These few files were created to help automatically pre fill Economic.
Entries are based on Google Calendar events and JIRA tasks currently assigned
to user and matching configurable filter. Duplicates are checked by
looking at task description (Economic) so it's safe to run this command
as many times a day as needed.

# Installation
Make sure you have `pip` installed on your system by calling:
`sudo apt-get install -y python-pip`

Once `pip` is installed run command below to install all required python libraries:
`sudo pip install -r requirements.txt`

After that rename `config.ini.dist` to `config.ini` and update it with all required
credentials for JIRA, Economic and Google API credentials from Google Developer Console.

# Usage
Calling `python run.py` will create all economic entries for today.
What's left is to update hours spent on each task in economic.

On first run you'll be asked to grant privileges to read your Google Calendars.

Due to application's limitations (see below) it advised to add new entry
in crontab to make sure all tasks will be registered:
`1 8-17 * * 1-5 root python /path/to/run.py >/dev/null 2>&1`

# Known limitations
* adding JIRA tasks for day other than current is not supported (might be tricky),
