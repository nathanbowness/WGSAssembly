import os


class CustomValues:
    # none
    ftp_password = 'xt5X6NvC'
    ftp_user = 'koziola'


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


class ExternalFolderNames:
    @staticmethod
    def get_names():
        """Returns a list of the possible folder names that are on the nas"""
        # does not include the structure to Non Food

        return ["BUR", "CAL", "DAR", "GTA", "HC_LON", "OLF", "STH"]
