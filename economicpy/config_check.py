from __future__ import print_function
try:
    import ConfigParser as configparser
except ImportError:
    import configparser
import os


class ConfigCheck(object):

    """
    Class used to validate configuration file against sample config.

    It's role is to check whether all required options are set.

    :param config_dist: str
    :param config_ini: str
    :raise Exception:
    """

    def __init__(self, config_dist, config_ini):
        """
        Set path for dist and custom configuration files.

        :param config_dist: file path
        :param config_ini: file path
        """
        self.config_dist = config_dist
        self.config_ini = config_ini
        if not os.path.isfile(self.config_ini):
            raise Exception('Configuration file config.ini not found.')
        if not os.path.isfile(self.config_dist):
            raise Exception('Configuration file config.ini.dist not found.')

    @staticmethod
    def make_list(tuples):
        """
        Create list of first elements in given list of tuples.

        :param tuples: list of tuples
        :return: list
        """
        return [item[0] for item in tuples]

    def find_differences(self, dist_items, ini_items):
        """
        Find and return differences between two lists of settings.

        :param dist_items: list of tuples
        :param ini_items: list of tuples
        """
        ini_keys = self.make_list(ini_items)
        dist_keys = self.make_list(dist_items)
        missing_dist = list(set(dist_keys) - set(ini_keys))
        missing_ini = list(set(ini_keys) - set(dist_keys))
        if missing_dist:
            print('Missing settings: %s' % ', '.join(missing_dist))
        if missing_ini:
            print('Not needed settings: %s' % ', '.join(missing_ini))

    def check_sections(self, sections):
        """
        Check whether number of config options is same in both files.

        :param sections: list of section names to check in both files.
        :return boolean
        """
        dist = configparser.ConfigParser()
        dist.read(self.config_dist)
        ini = configparser.ConfigParser()
        ini.read(self.config_ini)
        for section in sections:
            dist_items = dist.items(section)
            ini_items = ini.items(section)
            if len(dist_items) != len(ini_items):
                print('Section [%s] in configuration file does not contain all required settings' % section)
                self.find_differences(dist_items, ini_items)

                return False

        return True
