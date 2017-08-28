from RedmineAPI.Utilities import FileExtension, create_time_log
from RedmineAPI.Access import RedmineAccess
from RedmineAPI.Configuration import Setup

from Utilities import CustomKeys, CustomValues
from FTPValidation import Validation
from FTP import ServerInfo
from FTPDownload import Download
from FTPUpload import Upload
from FileAssembly import Assembly


class Automate(object):

    def __init__(self, force):

        # create a log, can be written to as the process continues
        self.timelog = create_time_log(FileExtension.runner_log)

        # Key: used to index the value to the config file for setup
        # Value: 3 Item Tuple ("default value", ask user" - i.e. True/False, "type of value" - i.e. str, int....)
        # A value of None is the default for all parts except for "Ask" which is True
        custom_terms = {CustomKeys.ftp_user: (CustomValues.ftp_user, True, str),
                        CustomKeys.ftp_password: (CustomValues.ftp_password, True, str)}

        # Create a RedmineAPI setup object to create/read/write to the config file and get default arguments
        setup = Setup(time_log=self.timelog, custom_terms=custom_terms)
        setup.set_api_key(force)

        # Custom terms saved to the config after getting user input
        self.custom_values = setup.get_custom_term_values()
        self.ftp_username = self.custom_values[CustomKeys.ftp_user]
        self.ftp_password = self.custom_values[CustomKeys.ftp_password]

        # Default terms saved to the config after getting user input
        self.seconds_between_checks = setup.seconds_between_check
        self.nas_mnt = setup.nas_mnt
        self.redmine_api_key = setup.api_key

        # Initialize Redmine wrapper
        self.access_redmine = RedmineAccess(self.timelog, self.redmine_api_key)

        self.botmsg = '\n\n_I am a bot. This action was performed automatically._'  # sets bot message
        # Subject name and Status to be searched on Redmine
        self.issue_title = 'wgs assembly'
        self.issue_status = 'New'

    def timed_retrieve(self):
        """
        Continuously search Redmine in intervals of the inputted time period, 
        Log errors to the log file as they occur
        """
        import time
        while True:
            # Get issues matching the issue status and subject
            found_issues = self.access_redmine.retrieve_issues(self.issue_status, self.issue_title)
            # Respond to the issues in the list 1 at a time
            while len(found_issues) > 0:
                self.respond_to_issue(found_issues.pop(len(found_issues) - 1))
            self.timelog.time_print("Waiting for the next check.")
            time.sleep(self.seconds_between_checks)

    def respond_to_issue(self, issue):
        """
        Run the desired automation process on the inputted issue
        :param issue: Specified Redmine issue to run the desired process on
        """
        self.timelog.time_print("Found a request to run. Subject: %s. ID: %s" % (issue.subject, issue.id))
        self.timelog.time_print("Adding to the list of responded to requests.")
        self.access_redmine.log_new_issue(issue)

        try:
            # Initialize all needed object to run the WGS Assembly process
            ftp_server = ServerInfo(self.ftp_username, self.ftp_password, issue)
            ftp_download = Download(ftp_server, issue, self.timelog)
            ftp_validation = Validation(ftp_server, ftp_download.samplesheet_path, self.timelog)
            assembly = Assembly(self.nas_mnt, self.timelog, ftp_server)
            ftp_upload = Upload(ftp_server, self.timelog)

            is_validated = ftp_validation.validate_upload()
            if is_validated is True:

                # Set the issue to in progress, while the files start downloading
                issue.redmine_msg = ("Beginning download of all files from the folder: %s on the FTP Server."
                                     % ftp_server.folder_name) + self.botmsg
                self.access_redmine.update_status_inprogress(issue)

                # download all files from the FTP Server to proper MiSeq_Backup location on the nas
                download_dir = ftp_download.download_all_files(self.nas_mnt)

                issue.redmine_msg = "Ftp files were downloaded to %s." % str(download_dir)
                self.access_redmine.update_status_inprogress(issue)

                # All files need to be linked to the "To_Assemble" folder
                assembly.create_symbolic_link(download_dir)
                assembly_done = assembly.wait_for_assembly()

                if assembly_done:
                    # Move the folder to the proper section on the nas and zip the results intended for Redmine
                    wgs_dir = assembly.move_to_wgsspades()
                    zip_path = assembly.zip_wgsspades_files(wgs_dir)
                    # Upload the zip file to Redmine
                    self.access_redmine.redmine_api.upload_file(zip_path, issue.id, 'application/zip',
                                                                file_name_once_uploaded=ftp_server.folder_name+".zip")
                    self.timelog.time_print("Uploaded zip file to the request on Redmine for issue: %s" % str(issue.id))

                    # Create the zip file intended to be uploaded to the ftp server and upload it
                    ftp_upload.create_ftp_zip_file(wgs_dir)
                    # ftp_upload.upload_zip_file()

                    # Update the author that the issue task has been completed
                    self.completed_response(issue, wgs_dir, ftp_validation.improper_files)
                else:
                    TimeoutError("The assembly process took longer than 6 hours. The automation process has timed out")
            else:
                self.completed_response(issue, "", ftp_validation.improper_files)

        except Exception as e:
            import traceback
            self.timelog.time_print("[Warning] the automation process had a problem, continuing redmine api anyways.")
            self.timelog.time_print("[WGS Assembly Error Dump]\n" + traceback.format_exc())
            # Send response
            issue.redmine_msg = "There was a problem with your request. Please create a new issue on" \
                                " Redmine to re-run it.\n%s" % traceback.format_exc()
            # Set it to feedback and assign it back to the author
            self.access_redmine.update_issue_to_author(issue, self.botmsg)

    def completed_response(self, issue, wgs_dir, missing_files):
        """
        Update the issue back to the author once the process has finished
        :param issue: Specified Redmine issue the process has been completed on
        :param wgs_dir" Directory where the WGS Assembly files were stored in the nas
        :param missing_files: All files that were not correctly uploaded
        """

        # Assign the issue back to the Author
        self.timelog.time_print("Assigning the issue: %s back to the author." % str(issue.id))

        if len(missing_files) > 0 and wgs_dir == "":
            issue.redmine_msg = "Not all files on the FTP server matched with the files on the Sample Sheet. " \
                                "Please submit a new Redmine Request where the naming issues of the following " \
                                "files are fixed:\n"
            for file in missing_files:
                issue.redmine_msg += file + '\n'
        else:
            issue.redmine_msg = "The assembly files have been moved to the proper WGSspades folder, they are " \
                                "stored at %s on the nas." % wgs_dir

        # Update author on redmine
        self.access_redmine.update_issue_to_author(issue, self.botmsg)

        # Log the completion of the issue including the message sent to the author
        self.timelog.time_print("\nMessage to author - %s\n" % issue.redmine_msg)
        self.timelog.time_print("Completed Response to issue %s." % str(issue.id))
        self.timelog.time_print("The next request will be processed once available")
