import os
import pycurl
from Utilities import UtilityMethods


class Download(object):

    def __init__(self, ftp_server, issue, timelog):
        self.timelog = timelog
        self.ftp_server = ftp_server
        self.undownloaded_files = list()

        temp_files = 'temp_files'

        # Create temporary path for the files to be stored
        dir_path = os.path.dirname(os.path.realpath(__file__))
        UtilityMethods.create_dir(dir_path, temp_files + '/' + str(issue.id))
        self.samplesheet_path = os.path.join(dir_path, temp_files, str(issue.id), 'SampleSheet.csv')

        self.download_sample_sheet()

    def download_sample_sheet(self):
        """
        Download the SampleSheet from within the specified folder on Redmine to be used later to validate 
        the uploaded sequences
        """

        # specific path for the SampleSheet within the given folder
        ftp_samplesheet = os.path.join(self.ftp_server.destinationurl, 'SampleSheet.csv')

        with open(self.samplesheet_path, 'wb') as localfile:
            curldownload = pycurl.Curl()
            curldownload.setopt(pycurl.URL, ftp_samplesheet)
            curldownload.setopt(pycurl.WRITEDATA, localfile)
            try:
                curldownload.perform()
                curldownload.close()
            except ConnectionError as e:
                print('There was an error finding the SampleSheet.csv on the ftp server - %s' % e.args[0])

    def download_all_files(self, nas_mnt):
        """
        Identify the proper folder for the files from the ftp server to be downloaded to
        Then download all the files
        :return: The place where the files were downloaded
        """
        self.timelog.time_print("Beginning download process for all files from the folder: %s on the FTP Server."
                                % self.ftp_server.folder_name)

        if self.ftp_server.lab_name is "SEQ":
            download_dir = os.path.join(nas_mnt, "MiSeq_Backup", self.ftp_server.folder_name)

        elif self.ftp_server.lab_name is not None:
            download_dir = os.path.join(nas_mnt, "External_MiSeq_Backup", self.ftp_server.lab_name,
                                        self.ftp_server.folder_name)
        else:
            download_dir = os.path.join(nas_mnt, "External_MiSeq_Backup", 'na', self.ftp_server.folder_name)

        self.download_ftp_folder(download_dir)
        return str(download_dir)

    def download_ftp_folder(self, download_dir):
        """
        Download each file that is in the specified folder on Redmine to the correct MiSeq_Backup folder in the nas
        :param download_dir: Proper MiSeq_Backup folder on the nas - either local or external
        """

        # Create the directory to download files - if it does not exist already
        UtilityMethods.create_dir(download_dir)

        for file in self.ftp_server.all_files:

            local_file = os.path.join(download_dir, file)
            ftp_file = os.path.join(self.ftp_server.destinationurl, file)

            with open(local_file, 'wb') as localfile:

                # Create a pycurl instance to download the file
                curldownload = pycurl.Curl()
                # Set the url to the ftp server path
                curldownload.setopt(curldownload.URL, ftp_file)
                # Write the data to a file
                curldownload.setopt(curldownload.WRITEDATA, localfile)

                try:
                    self.timelog.time_print("   Downloading file: %s into directory: %s" % (file, download_dir))
                    curldownload.perform()
                    curldownload.close()
                except ConnectionError as e:
                    self.undownloaded_files.append(file)
                    self.timelog.time_print('There was an error finding the file %s on the ftp server. Error: %s' %
                                            (file, e.args[0]))
