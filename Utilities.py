import os
import datetime
from pyaccessories.TimeLog import Timer

class CustomValues:
    # none
    ftp = None

class CustomKeys:

    # Config Json Keys
    ftp_user = 'ftp_username'
    ftp_password = 'ftp_password'


class UtilityMethods:
    @staticmethod
    def create_dir(basepath, path_ext=""):
        """ Creates the the output directory if it doesn't exist """
        if not os.path.exists(os.path.join(basepath, path_ext)):
            os.makedirs(os.path.join(basepath, path_ext))