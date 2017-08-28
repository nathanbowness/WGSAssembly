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
        self.lab_name = None

        self.all_files = self.get_file_names()
        self.get_lab_name()

    def get_file_names(self):
        """
        Return a list of all the files names that were uploaded on the ftp server in the folder specified on Redmine
        """
        curl = pycurl.Curl()
        output = BytesIO()

        # Iterate through the path for files given on the ftp server
        curl.setopt(curl.URL, self.destinationurl+"/")

        # Write the output to ioreader in bytes
        curl.setopt(curl.WRITEFUNCTION, output.write)

        curl.perform()
        curl.close()
        ftp_files = list()

        # Each different file information is seperated by a \n character, encoded in bytes so must be decoded
        lines = output.getvalue().decode('utf-8').split('\n')
        for line in lines:
            if line:
                # The last element of the line is the filename
                ftp_files.append(line.split()[-1].rstrip())

        return ftp_files

    def get_lab_name(self):
        """
        Set the lab name abbreviation to be used for the file location in the nas
        """
        self.set_local_lab_name()

        if self.lab_name is None:
            self.set_external_lab_name()

    def set_local_lab_name(self):
        """
        Check and set the lab name to the proper local abbreviation if the files include 'SEQ' in more than 4 file names
        """
        local_name = "SEQ"
        tracker = 0

        for file in self.all_files:

            # If 4 files are found with the local lab name in the file, download to the local lab folder in the nas
            if tracker > 3:
                self.lab_name = local_name
                break

            # If local lab lab in found in the file name, add an occurrence to the tracker
            if local_name in file:
                tracker += 1

    def set_external_lab_name(self, ):
        """
        Check and set the lab name to the proper external abbreviation if the files include any external abbreviation 
        in more than 4 file names
        """

        # Get possible external folder names to download the files into
        folder_names = ExternalFolderNames.get_names()
        # Generic initial lab name
        tracker = 0

        # For each lab, check to see if the files belong in that folder
        for name in folder_names:

            # Check each file name to see if it has the external lab abbreviation within it
            for file in self.all_files:
                if name in file:
                    tracker += 1

            # If 4 files are found with the external lab name in the file, or there are less than 4 files total
            # within the folder and any matches occur. Download to the external lab folder in the nas
            if tracker > 3 or (tracker > 0 and len(self.all_files) < 4):
                self.lab_name = name
                break

            # Reset if the above conditions are not satisfied and retry with the another lab name
            else:
                tracker = 0
