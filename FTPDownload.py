import os
import pycurl
from Utilities import UtilityMethods

# Author: Nathan Bowness, Modified from Adam Koziol's code -
# https://github.com/adamkoziol/SPAdesPipeline/blob/dev/OLCspades/ftpdownload.py


class Download(object):

    def __init__(self, ftp_server, issue, timelog):
        self.timelog = timelog
        self.ftp_server = ftp_server
        self.undownloaded_files = list()

        temp_files = 'temp_files'

        # create temp paths for the files to be stored    (locally for now  ->   maybe nas later)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        UtilityMethods.create_dir(dir_path, temp_files + '/' + str(issue.id))
        self.samplesheet_path = os.path.join(dir_path, temp_files, str(issue.id), 'SampleSheet.csv')

        self.download_sample_sheet()

    def download_sample_sheet(self):

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

    def download_all_files(self, nas_mnt, all_files):
        """
        Download all files from the ftp server to the Nas in the proper External MySEQ folder
        :return:
        """
        # Get the internal lab folder directory in the nas where the ftp files should be downloaded
        download_dir = self.ftp_server.get_local_lab_path(nas_mnt, "MiSeq_Backup", all_files)

        if download_dir is None:
            # Get the external lab folder directory in the nas where the ftp files should be downloaded
            download_dir = self.ftp_server.get_external_lab_path(nas_mnt, "External_MiSeq_Backup", all_files)

        if download_dir is None:
            # Create the path to download files that cannot be validated according to their
            # lab abbreviation in the filename
            download_dir = os.path.join(nas_mnt, "External_MiSeq_Backup", 'na', self.ftp_server.folder_name)

        self.download_ftp_folder(download_dir, all_files)
        msg = str(download_dir)

        return msg

    def download_ftp_folder(self, download_dir, ftp_files):

        # download_dir = "/home/bownessn/Documents/Test_WGS/" # -> For testing

        # Create the directory to download files - if it does not exist
        UtilityMethods.create_dir(download_dir)

        for file in ftp_files:

            local_file = os.path.join(download_dir, file)
            ftp_file = os.path.join(self.ftp_server.destinationurl, 'SampleSheet.csv')

            with open(local_file, 'wb') as localfile:

                # Create a pycurl instance to download the file
                curldownload = pycurl.Curl()
                # Set the url to the ftp server path
                curldownload.setopt(curldownload.URL, ftp_file)
                # Write the data to the download file
                curldownload.setopt(curldownload.WRITEDATA, localfile)

                try:
                    self.timelog.time_print("Downloading file: %s into directory: %s" % (file, download_dir))
                    curldownload.perform()
                    curldownload.close()
                except ConnectionError as e:
                    self.undownloaded_files.append(file)
                    self.timelog.time_print('There was an error finding the file %s on the ftp server. Error: %s' %
                                            (file, e.args[0]))
