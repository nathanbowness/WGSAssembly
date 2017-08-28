import pycurl
import zipfile
import os
import shutil


class Upload:

    def __init__(self, ftp_server, timelog):

        self.username = ftp_server.username
        self.password = ftp_server.password
        self.folder_name = ftp_server.folder_name
        self.timelog = timelog

        # Path to the outgoing folder on the ftp server where the zip file should be place
        self.uploadpath = 'ftp.agr.gc.ca/outgoing/cfia-ak/' + self.folder_name

        # Create a URL that includes the user name and password, so PycURL can login to the FTP server
        self.destinationurl = 'ftp://{}:{}@{}'.format(self.username, self.password, self.uploadpath)

    def create_ftp_zip_file(self, wgs_dir):
        """
        Create the zip file that will be uploaded to the ftp server in the folder - /outgoing/cfia-ak/redminefoldername
        It will contain the 'Reports' and 'BestAssemblies' folders from the results of run 
        :param wgs_dir: The WGSspades directory where the assembly result files can be located on the nas
        """

        # folders to be zipped into the ftp results that will be uploaded
        folder_list = ["reports", "BestAssemblies"]
        # Name of the zip file
        zip_file_name = self.folder_name + "_ftp_results.zip"

        zip_path = os.path.join(wgs_dir, zip_file_name)
        self.timelog.time_print("Creating zip file %s" % zip_path)

        # If for some reason the zip file already exists due to a re-run, delete the old one
        if os.path.isdir(zip_path):
            shutil.rmtree(zip_path)

        # Create the zip file to be written to
        zip_file = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)

        # For every folder to be added to the zip file, add all files within it and log the process
        for folder in folder_list:
            self.timelog.time_print("   Folder \'%s\' - added to the zip file." % folder)
            try:
                for dirpath, dirs, files in os.walk(os.path.join(wgs_dir, folder)):
                    for f in files:
                        zip_file.write(os.path.join(dirpath, f), arcname=os.path.join(folder, f))
                        self.timelog.time_print("       Files: %s - added to the folder." % f)
            except FileNotFoundError:
                self.timelog.time_print("[Warning] Can't find %s, will leave it out of .zip" % folder)
                raise

        zip_file.close()

    def upload_zip_file(self):
        """
        This method is not implemented but should use pycurl or some other library to upload the ftp zip file to the 
        ftp server in the designated location shown above
        """
        print("Upload the zip file to the ftp server.")
        # # Creating the curl object to upload
        # curl = pycurl.Curl()
        #
        # curl.setopt(pycurl.URL, os.path.join(self.destinationurl, zip_file_name))
        #
        # curl.setopt(curl.HTTPPOST, [
        #     ('fileupload', (
        #         # upload the contents of this file
        #         curl.FORM_BUFFER, zip_file,
        #     )),
        # ])
        #
        # curl.perform()
        # curl.close()


