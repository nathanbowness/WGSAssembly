import os
import pycurl
from io import BytesIO
from Utilities import UtilityMethods
import csv

# Author: Nathan Bowness, Modified from Adam Koziol's code -
# https://github.com/adamkoziol/SPAdesPipeline/blob/dev/OLCspades/ftpdownload.py

class FTPDownload(object):

    def __init__(self, username, password, issue):
        self.username = username
        self.password = password
        self.validated_files = list()
        self.improper_files = list()

        temp_files = 'temp_files'

        # TODO make this come in as part of the request
        self.downloadpath = 'ftp.agr.gc.ca/incoming/cfia-ak/BUR_2017-06-30/'

        # Create a URL that includes the user name and password, so PycURL can login to the FTP server
        self.destinationurl = 'ftp://{}:{}@{}'.format(self.username, self.password, self.downloadpath)

        # create temp paths for the files to be stored    (locally for now  ->   maybe nas later)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        UtilityMethods.create_dir(dir_path, temp_files + '/' + str(issue.id))
        self.samplesheet_path = os.path.join(dir_path, temp_files, str(issue.id), 'SampleSheet.csv')

    def ftp_validate_upload(self):
        """
        Comment
        """
        self.download_samplesheet()
        self.validate_uploaded_files()
        print()

    def download_samplesheet(self):

        # specific path for the SampleSheet within the given folder
        ftp_samplesheet = os.path.join(self.destinationurl, 'SampleSheet.csv')

        with open(self.samplesheet_path, 'wb') as localfile:
            curldownload = pycurl.Curl()
            curldownload.setopt(pycurl.URL, ftp_samplesheet)
            curldownload.setopt(pycurl.WRITEDATA, localfile)
            try:
                curldownload.perform()
                curldownload.close()
            except ConnectionError as e:
                print('There was an error finding the SampleSheet.csv on the ftp server - %s' % e.args[0])

    def validate_uploaded_files(self):
        """
        Comment
        """
        ftp_names = self.get_ftp_files_names()
        samplesheet_names = self.get_samplesheet_names()
        self.match_results(ftp_names, samplesheet_names)


    def get_ftp_files_names(self):
        curl = pycurl.Curl()

        # iterate through the path for files given on the ftp server
        curl.setopt(pycurl.URL, self.destinationurl)
        output = BytesIO()
        # write the output the the ioreader in bytes
        curl.setopt(pycurl.WRITEFUNCTION, output.write)
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

    def get_samplesheet_names(self):
        regex = r'^(2\d{3}-\w{2,10}-\d{3,4})$'
        import re
        csv_names = list()
        found = False

        with open(self.samplesheet_path, 'r') as input_file:
            reader = csv.reader(input_file, delimiter=',')
            for row in reader:
                if row:
                    # iterate through the document unto 'Sample_ID' is found in the first column
                    if 'Sample_ID' in row[0]:
                        found = True
                        continue

                    # once past the 'Sample_ID' add any SeqID to the list of files names
                    if found:
                        if re.match(regex, row[0]):
                            csv_names.append(row[0].rstrip())
                        else:
                            # if the proper format is not found append them to the list
                            self.improper_files.append(row[0].rstrip())
        return csv_names

    def match_results(self, ftp_names, samplesheet_names):

        for samplesheet_name in samplesheet_names:
            count = 0
            pair_found = False

            # search for 2 files matching the SeqID given in the Sample sheet on the ftp server files
            for ftp_name in ftp_names:
                if samplesheet_name in ftp_name:
                    count += 1
                    # if 2 are found, then
                    if count == 2:
                        self.validated_files.append(samplesheet_name)
                        pair_found = True
            # if 2 are not found, then add the name to improper files
            if not pair_found:
                self.improper_files.append(samplesheet_name)
                # TODO possibly log that the files does not contain 2 pairs
