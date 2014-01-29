# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import cherrypy
import os.path
import datetime
import re

from sickbeard import helpers
from sickbeard import logger
from sickbeard import naming
from sickbeard import db

import sickbeard

naming_ep_type = ("%(seasonnumber)dx%(episodenumber)02d",
                  "s%(seasonnumber)02de%(episodenumber)02d",
                   "S%(seasonnumber)02dE%(episodenumber)02d",
                   "%(seasonnumber)02dx%(episodenumber)02d")
naming_ep_type_text = ("1x02", "s01e02", "S01E02", "01x02")

naming_multi_ep_type = {0: ["-%(episodenumber)02d"] * len(naming_ep_type),
                        1: [" - " + x for x in naming_ep_type],
                        2: [x + "%(episodenumber)02d" for x in ("x", "e", "E", "x")]}
naming_multi_ep_type_text = ("extend", "duplicate", "repeat")

naming_sep_type = (" - ", " ")
naming_sep_type_text = (" - ", "space")

def change_HTTPS_CERT(https_cert):

    if https_cert == '':
        sickbeard.HTTPS_CERT = ''
        return True

    if os.path.normpath(sickbeard.HTTPS_CERT) != os.path.normpath(https_cert):
        if helpers.makeDir(os.path.dirname(os.path.abspath(https_cert))):
            sickbeard.HTTPS_CERT = os.path.normpath(https_cert)
            logger.log(u"Changed https cert path to " + https_cert)
        else:
            return False

    return True


def change_HTTPS_KEY(https_key):

    if https_key == '':
        sickbeard.HTTPS_KEY = ''
        return True

    if os.path.normpath(sickbeard.HTTPS_KEY) != os.path.normpath(https_key):
        if helpers.makeDir(os.path.dirname(os.path.abspath(https_key))):
            sickbeard.HTTPS_KEY = os.path.normpath(https_key)
            logger.log(u"Changed https key path to " + https_key)
        else:
            return False

    return True


def change_LOG_DIR(log_dir, web_log):

    log_dir_changed = False
    abs_log_dir = os.path.normpath(os.path.join(sickbeard.DATA_DIR, log_dir))

    if os.path.normpath(sickbeard.LOG_DIR) != abs_log_dir:
        if helpers.makeDir(abs_log_dir):
            sickbeard.ACTUAL_LOG_DIR = os.path.normpath(log_dir)
            sickbeard.LOG_DIR = abs_log_dir

            logger.sb_log_instance.initLogging()
            logger.log(u"Initialized new log file in " + sickbeard.LOG_DIR)
            log_dir_changed = True

        else:
            return False

    if sickbeard.WEB_LOG != web_log or log_dir_changed == True:
        sickbeard.WEB_LOG = web_log

        if sickbeard.WEB_LOG == 1:
            cherry_log = os.path.join(sickbeard.LOG_DIR, "cherrypy.log")
            logger.log(u"Change cherry log file to " + cherry_log)
        else:
            cherry_log = None
            logger.log(u"Disable cherry logging")

        cherrypy.config.update({'log.access_file': cherry_log})

    return True


def change_NZB_DIR(nzb_dir):

    if nzb_dir == '':
        sickbeard.NZB_DIR = ''
        return True

    if os.path.normpath(sickbeard.NZB_DIR) != os.path.normpath(nzb_dir):
        if helpers.makeDir(nzb_dir):
            sickbeard.NZB_DIR = os.path.normpath(nzb_dir)
            logger.log(u"Changed NZB folder to " + nzb_dir)
        else:
            return False

    return True


def change_TORRENT_DIR(torrent_dir):

    if torrent_dir == '':
        sickbeard.TORRENT_DIR = ''
        return True

    if os.path.normpath(sickbeard.TORRENT_DIR) != os.path.normpath(torrent_dir):
        if helpers.makeDir(torrent_dir):
            sickbeard.TORRENT_DIR = os.path.normpath(torrent_dir)
            logger.log(u"Changed torrent folder to " + torrent_dir)
        else:
            return False

    return True


def change_TV_DOWNLOAD_DIR(tv_download_dir):

    if tv_download_dir == '':
        sickbeard.TV_DOWNLOAD_DIR = ''
        return True

    if os.path.normpath(sickbeard.TV_DOWNLOAD_DIR) != os.path.normpath(tv_download_dir):
        if helpers.makeDir(tv_download_dir):
            sickbeard.TV_DOWNLOAD_DIR = os.path.normpath(tv_download_dir)
            logger.log(u"Changed TV download folder to " + tv_download_dir)
        else:
            return False

    return True


def change_SEARCH_FREQUENCY(freq):

    if freq == None:
        freq = sickbeard.DEFAULT_SEARCH_FREQUENCY
    else:
        freq = int(freq)

    if freq < sickbeard.MIN_SEARCH_FREQUENCY:
        freq = sickbeard.MIN_SEARCH_FREQUENCY

    sickbeard.SEARCH_FREQUENCY = freq

    sickbeard.currentSearchScheduler.cycleTime = datetime.timedelta(minutes=sickbeard.SEARCH_FREQUENCY)
    sickbeard.backlogSearchScheduler.cycleTime = datetime.timedelta(minutes=sickbeard.get_backlog_cycle_time())


def change_VERSION_NOTIFY(version_notify):
   
    oldSetting = sickbeard.VERSION_NOTIFY

    sickbeard.VERSION_NOTIFY = version_notify

    if version_notify == False:
        sickbeard.NEWEST_VERSION_STRING = None;
        
    if oldSetting == False and version_notify == True:
        sickbeard.versionCheckScheduler.action.run() #@UndefinedVariable


def CheckSection(CFG, sec):
    """ Check if INI section exists, if not create it """
    try:
        CFG[sec]
        return True
    except:
        CFG[sec] = {}
        return False

################################################################################
# Check_setting_int                                                            #
################################################################################
def minimax(val, low, high):
    """ Return value forced within range """
    try:
        val = int(val)
    except:
        val = 0
    if val < low:
        return low
    if val > high:
        return high
    return val


################################################################################
# Check_setting_int                                                            #
################################################################################
def check_setting_int(config, cfg_name, item_name, def_val):
    try:
        my_val = int(config[cfg_name][item_name])
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = my_val
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val
    logger.log(item_name + " -> " + str(my_val), logger.DEBUG)
    return my_val


################################################################################
# Check_setting_float                                                          #
################################################################################
def check_setting_float(config, cfg_name, item_name, def_val):
    try:
        my_val = float(config[cfg_name][item_name])
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = my_val
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val

    logger.log(item_name + " -> " + str(my_val), logger.DEBUG)
    return my_val


################################################################################
# Check_setting_str                                                            #
################################################################################
def check_setting_str(config, cfg_name, item_name, def_val, log=True):

    # For passwords you must include the word `password` in the item_name and add `helpers.encrypt(ITEM_NAME, ENCRYPTION_VERSION)` in save_config()
    if bool(item_name.find('password') + 1):
        encryption_version = sickbeard.ENCRYPTION_VERSION
    else:
        encryption_version = 0
        
    try:
        my_val = helpers.decrypt(config[cfg_name][item_name], encryption_version)
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = helpers.encrypt(my_val, encryption_version)
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = helpers.encrypt(my_val, encryption_version)

    if log:
        logger.log(item_name + " -> " + str(my_val), logger.DEBUG)
    else:
        logger.log(item_name + " -> ******", logger.DEBUG)
    return my_val

class ConfigMigrator():

    def __init__(self, config_obj):
        """
        Initializes a config migrator that can take the config from the version indicated in the config
        file up to the version required by SB
        """
        
        self.config_obj = config_obj

        # check the version of the config
        self.config_version = check_setting_int(config_obj, 'General', 'config_version', sickbeard.CONFIG_VERSION)
        self.expected_config_version = sickbeard.CONFIG_VERSION
        self.migration_names = {1: 'Custom naming',
                                2: 'Sync backup number with version number',
                                3: 'Rename omgwtfnzb variables',
                                4: 'Add newznab catIDs'
                                } 


    def migrate_config(self):
        """
        Calls each successive migration until the config is the same version as SB expects
        """

        if self.config_version > self.expected_config_version:
            logger.log_error_and_exit(u"Your config version (" + str(self.config_version) + ") has been incremented past what this version of Sick Beard supports (" + str(self.expected_config_version) + ").\n" + \
                                      "If you have used other forks or a newer version of Sick Beard, your config file may be unusable due to their modifications.")
        
        sickbeard.CONFIG_VERSION = self.config_version
        
        while self.config_version < self.expected_config_version:

            next_version = self.config_version + 1
            
            if next_version in self.migration_names:
                migration_name = ': ' + self.migration_names[next_version]
            else:
                migration_name = ''
            
            logger.log(u"Backing up config before upgrade")
            if not helpers.backupVersionedFile(sickbeard.CONFIG_FILE, self.config_version):
                logger.log_error_and_exit(u"Config backup failed, abort upgrading config")
            else:
                logger.log(u"Proceeding with upgrade")  
            
            # do the migration, expect a method named _migrate_v<num>
            logger.log(u"Migrating config up to version " + str(next_version) + migration_name)
            getattr(self, '_migrate_v' + str(next_version))()
            self.config_version = next_version

            # save new config after migration
            sickbeard.CONFIG_VERSION = self.config_version
            logger.log(u"Saving config file to disk")
            sickbeard.save_config()

    # Migration v1: Custom naming 
    def _migrate_v1(self):
        """
        Reads in the old naming settings from your config and generates a new config template from them.
        """

        sickbeard.NAMING_PATTERN = self._name_to_pattern()
        logger.log("Based on your old settings I'm setting your new naming pattern to: " + sickbeard.NAMING_PATTERN)

        sickbeard.NAMING_CUSTOM_ABD = bool(check_setting_int(self.config_obj, 'General', 'naming_dates', 0))

        if sickbeard.NAMING_CUSTOM_ABD:
            sickbeard.NAMING_ABD_PATTERN = self._name_to_pattern(True)
            logger.log("Adding a custom air-by-date naming pattern to your config: " + sickbeard.NAMING_ABD_PATTERN)
        else:
            sickbeard.NAMING_ABD_PATTERN = naming.name_abd_presets[0]

        sickbeard.NAMING_MULTI_EP = int(check_setting_int(self.config_obj, 'General', 'naming_multi_ep_type', 1))

        # see if any of their shows used season folders
        myDB = db.DBConnection()
        season_folder_shows = myDB.select("SELECT * FROM tv_shows WHERE flatten_folders = 0")

        # if any shows had season folders on then prepend season folder to the pattern
        if season_folder_shows:

            old_season_format = check_setting_str(self.config_obj, 'General', 'season_folders_format', 'Season %02d')

            if old_season_format:
                try:
                    new_season_format = old_season_format % 9
                    new_season_format = new_season_format.replace('09', '%0S')
                    new_season_format = new_season_format.replace('9', '%S')

                    logger.log(u"Changed season folder format from " + old_season_format + " to " + new_season_format + ", prepending it to your naming config")
                    sickbeard.NAMING_PATTERN = new_season_format + os.sep + sickbeard.NAMING_PATTERN

                except (TypeError, ValueError):
                    logger.log(u"Can't change " + old_season_format + " to new season format", logger.ERROR)

        # if no shows had it on then don't flatten any shows and don't put season folders in the config
        else:

            logger.log(u"No shows were using season folders before so I'm disabling flattening on all shows")

            # don't flatten any shows at all
            myDB.action("UPDATE tv_shows SET flatten_folders = 0")

        sickbeard.NAMING_FORCE_FOLDERS = naming.check_force_season_folders()

    def _name_to_pattern(self, abd=False):

        # get the old settings from the file
        use_periods = bool(check_setting_int(self.config_obj, 'General', 'naming_use_periods', 0))
        ep_type = check_setting_int(self.config_obj, 'General', 'naming_ep_type', 0)
        sep_type = check_setting_int(self.config_obj, 'General', 'naming_sep_type', 0)
        use_quality = bool(check_setting_int(self.config_obj, 'General', 'naming_quality', 0))

        use_show_name = bool(check_setting_int(self.config_obj, 'General', 'naming_show_name', 1))
        use_ep_name = bool(check_setting_int(self.config_obj, 'General', 'naming_ep_name', 1))

        # make the presets into templates
        naming_ep_type = ("%Sx%0E",
                          "s%0Se%0E",
                          "S%0SE%0E",
                          "%0Sx%0E")
        naming_sep_type = (" - ", " ")

        # set up our data to use
        if use_periods:
            show_name = '%S.N'
            ep_name = '%E.N'
            ep_quality = '%Q.N'
            abd_string = '%A.D'
        else:
            show_name = '%SN'
            ep_name = '%EN'
            ep_quality = '%QN'
            abd_string = '%A-D'

        if abd:
            ep_string = abd_string
        else:
            ep_string = naming_ep_type[ep_type]

        finalName = ""

        # start with the show name
        if use_show_name:
            finalName += show_name + naming_sep_type[sep_type]

        # add the season/ep stuff
        finalName += ep_string

        # add the episode name
        if use_ep_name:
            finalName += naming_sep_type[sep_type] + ep_name

        # add the quality
        if use_quality:
            finalName += naming_sep_type[sep_type] + ep_quality

        if use_periods:
            finalName = re.sub("\s+", ".", finalName)

        return finalName

    # Migration v2: Dummy migration to sync backup number with config version number
    def _migrate_v2(self):
        return
 
    # Migration v2: Rename  omgwtfnzb variables
    def _migrate_v3(self):
        """
        Reads in the old naming settings from your config and generates a new config template from them.
        """
        # get the old settings from the file and store them in the new variable names
        sickbeard.OMGWTFNZBS_USERNAME = check_setting_str(self.config_obj, 'omgwtfnzbs', 'omgwtfnzbs_uid', '')
        sickbeard.OMGWTFNZBS_APIKEY = check_setting_str(self.config_obj, 'omgwtfnzbs', 'omgwtfnzbs_key', '')

    # Migration v4: Add default newznab catIDs
    def _migrate_v4(self):
        """ Update newznab providers so that the category IDs can be set independently via the config """

        new_newznab_data = []
        old_newznab_data = check_setting_str(self.config_obj, 'Newznab', 'newznab_data', '')

        if old_newznab_data:
            old_newznab_data_list = old_newznab_data.split("!!!")

            for cur_provider_data in old_newznab_data_list:
                try:
                    name, url, key, enabled = cur_provider_data.split("|")
                except ValueError:
                    logger.log(u"Skipping Newznab provider string: '" + cur_provider_data + "', incorrect format", logger.ERROR)
                    continue

                if name == 'Sick Beard Index':
                    key = '0'

                if name == 'NZBs.org':
                    catIDs = '5030,5040,5070,5090'
                else:
                    catIDs = '5030,5040'

                cur_provider_data_list = [name, url, key, catIDs, enabled]
                new_newznab_data.append("|".join(cur_provider_data_list))

            sickbeard.NEWZNAB_DATA = "!!!".join(new_newznab_data)          
            