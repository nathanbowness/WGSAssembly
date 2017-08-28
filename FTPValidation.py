import csv


class Validation:

    def __init__(self, ftp_server, samplesheet_path, timelog):
        self.ftp_server = ftp_server
        self.timelog = timelog
        self.validated_files = list()
        self.improper_files = list()

        self.samplesheet_path = samplesheet_path

    def validate_upload(self):
        """
        Validate the uploaded samplesheet and files by the lab
        :return If the files were properly uploaded return True, otherwise return False
        """

        samplesheet_names = self.get_samplesheet_names()
        self.match_results(samplesheet_names)

        if len(self.improper_files) is 0:
            # Successful upload
            return True
        # Unsuccessful upload
        return False

    def get_samplesheet_names(self):
        """
        Return a list of all the files names that were referenced in the SampleSheet
        """

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

    def match_results(self, samplesheet_names):
        """
        Match the file names from both inputs, if there are any files on the sample sheet not uploaded then add those
        files to the improper_files list
        :param samplesheet_names: List of file names that were referenced in the sample sheet
        :return: 
        """

        for samplesheet_name in samplesheet_names:
            count = 0
            pair_found = False

            # search for 2 files matching the SeqID given in the Sample sheet on the ftp server files
            for ftp_name in self.ftp_server.all_files:
                if samplesheet_name in ftp_name:
                    count += 1
                    # if 2 are found, then
                    if count == 2:
                        self.validated_files.append(samplesheet_name)
                        pair_found = True
                        break
            # if 2 are not found, then add the name to improper files
            if not pair_found:
                self.improper_files.append(samplesheet_name)
