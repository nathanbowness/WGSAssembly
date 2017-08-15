import os
import pycurl

from io import BytesIO
from Utilities import ExternalFolderNames


class ServerInfo(object):

    def __init__(self, username, password, issue):
        self.username = username
        self.password = password
        self.folder_name = issue.description.rstrip()

        self.downloadpath = 'ftp.agr.gc.ca/incoming/cfia-ak/' + self.folder_name

        # Create a URL that includes the user name and password, so PycURL can login to the FTP server
        self.destinationurl = 'ftp://{}:{}@{}'.format(self.username, self.password, self.downloadpath)

        self.all_files = self.get_file_names()
        self.lab_name = None

    def get_file_names(self):
        """
        Return a list of all the files names that were uploaded on the ftp server in the folder specified
        """
        curl = pycurl.Curl()
        output = BytesIO()

        # iterate through the path for files given on the ftp server
        curl.setopt(curl.URL, self.destinationurl+"/")

        # write the output the ioreader in bytes
        curl.setopt(curl.WRITEFUNCTION, output.write)

        curl.perform()
        curl.close()

        ftp_files = list()

        # each different file information is seperated by a \n character, encoded in bytes so must be decoded
        lines = output.getvalue().decode('utf-8').split('\n')
        for line in lines:
            if line:
                # the last element of the line is the filename
                ftp_files.append(line.split()[-1].rstrip())

        return ftp_files

    def get_external_lab_path(self, nas_mnt, external_folder, all_files):
        """
        Check the files uploaded for any of the external lab name abbreviations in the file name
        :return: The directory in the nas where the files are to be saved
        """

        # get possible external folder names to download the files into
        folder_names = ExternalFolderNames.get_names()
        # generic initial lab name
        tracker = 0
        save_dir = None

        # for each lab, check to see if the files belong in that folder
        for name in folder_names:

            # check each file name to see if it contracts the external lab abbreviation within it
            for file in all_files:
                if name in file:
                    tracker += 1

            # if 4 files are found with the external lab name in the file, Or there are less than 4 files any matches
            # Download to the external lab folder in the nas
            if tracker > 3 or (tracker > 0 and len(all_files) < 4):
                save_dir = os.path.join(nas_mnt, external_folder, name, self.folder_name)
                self.lab_name = name
                break

            # reset if the above conditions are not satisfied and retry with the another lab name
            else:
                tracker = 0

        return save_dir

    def get_local_lab_path(self, nas_mnt, local_folder, all_files):
        """
        Check the files uploaded for the local lab abbreviation in the file name
        :return: The directory in the nas where the files are to be saved
        """

        local_name = "SEQ"
        save_dir = None
        tracker = 0

        for file in all_files:

            # if 4 files are found with the local lab name in the file, download to the local lab folder in the nas
            if tracker > 3:
                self.lab_name = local_name
                save_dir = os.path.join(nas_mnt, local_folder, self.folder_name)
                break

            # if local lab lab in found in the file name, add an occurrence to the tracker
            if local_name in file:
                tracker += 1

        return save_dir
