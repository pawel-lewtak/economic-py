import ConfigParser
import os


class ConfigCheck(object):
    """
    Check if configuration file is up to date and contains all options
    mentioned in example configuration file.
    """

    def __init__(self, config_dist, config_ini):
        """
        Set path for dist and custom configuration files

        :param config_dist: file path
        :param config_ini: file path
        """
        self.config_dist = config_dist
        self.config_ini = config_ini
        if not os.path.isfile(self.config_ini):
            raise Exception('Configuration file config.ini not found.')
        if not os.path.isfile(self.config_dist):
            raise Exception('Configuration file config.ini.dist not found.')

    def check_sections(self, sections):
        """
            Checks whether number of config options is same in both files.

            :param sections: list of section names to check in both files.
            :return: boolean
            """
        dist = ConfigParser.ConfigParser()
        dist.read(self.config_dist)
        ini = ConfigParser.ConfigParser()
        ini.read(self.config_ini)
        for section in sections:
            dist_items = dist.items(section)
            ini_items = ini.items(section)
            if len(dist_items) != len(ini_items):
                print('Section [%s] in configuration file does not contain all required settings' % section)
                ini_keys = [k for k, v in ini_items]
                dist_keys = [k for k, v in dist_items]
                missing_dist = list(set(dist_keys) - set(ini_keys))
                missing_ini = list(set(ini_keys) - set(dist_keys))
                if missing_dist:
                    print('Missing settings: %s' % ', '.join(missing_dist))
                if missing_ini:
                    print('Not needed settings: %s' % ', '.join(missing_ini))
                return False

        return True