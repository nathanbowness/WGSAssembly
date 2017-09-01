import os
import time
import zipfile
import shutil
from Utilities import UtilityMethods
from distutils.dir_util import copy_tree


class Assembly:

    def __init__(self, nas_mnt, timelog, ftp_server):
        self.nas_mnt = nas_mnt
        self.timelog = timelog
        self.ftp_server = ftp_server
        self.assembly_dir = os.path.join(self.nas_mnt, "To_Assemble")

    def create_symbolic_link(self, download_dir):
        """
        Create a symbolic link for all files in the folder created on the nas to the "To_Assemble" folder
        The folder name is the same as the Inputted one from Redmine with the addition of "_Ready" on the end
        """

        self.timelog.time_print("Creating Symbolic links to the \"To_Assemble\" folder on the nas for all "
                                "the files that were downloaded.")

        assembly_ready_dir = os.path.join(self.assembly_dir, self.ftp_server.folder_name + "_Ready")

        # If the folder already exists, delete it - most likely a previous version
        # The ensure to create the folder again if it has been deleted or did not exist
        if os.path.isdir(assembly_ready_dir):
            shutil.rmtree(assembly_ready_dir)
        UtilityMethods.create_dir(assembly_ready_dir)

        for files in self.ftp_server.all_files:
            # Path where the file is currently stored and Path where the symbolic link will be put
            current_file_path = os.path.join(download_dir, files)
            dest_file_path = os.path.join(assembly_ready_dir, files)

            # Create a symbolic link from the current file directory to into the 'To_Assemble' folder
            os.symlink(current_file_path, dest_file_path)

    def wait_for_assembly(self):
        """
        Once the folder from the ftp has been moved to the 'To_Assemble' folder with the flag 'foldername_Ready'
        You must wait until a folder appears with the name 'foldername_Assembled' so show the the run has completed on
        the files you have put there. This method will wait for the assembled folder to exist for 6 hours before 
        timing out and updating the author with an error.
        :return: True if the folder exists within the time limit, False if the folder does not exist in the time limit
        """

        counter = 0
        assembly_done_dir = os.path.join(self.assembly_dir, self.ftp_server.folder_name + "_Assembled")

        self.timelog.time_print("Waiting for the assembly process to finish.")

        # Wait a total of 36 * 10 minutes = 360 minutes
        while counter < 36:
            if os.path.isdir(assembly_done_dir):
                # if the assembly process has completed, continue with the process
                self.timelog.time_print("The files have been assembled in the folder: %s" %
                                        (self.ftp_server.folder_name + "_Assembled"))
                return True
            # If the assembly process has not completed wait 10 minutes before another check
            counter += 1
            self.timelog.time_print("Still waiting for the assembly process to finish.")
            time.sleep(600)

        self.timelog.time_print("The files were not assembled within the time limit.")
        return False

    def wait_for_filecopy(self):
        """
        Once the 'foldername_Assembled' folder has been created, wait for all of the sequence folders to be copied
        to the directory before continuing the process. Wait a maximum of 20 minutes before timing out and giving 
        an error - the copying should not take that long
        """
        time.sleep(1200)
        return True

    def move_to_wgsspades(self):
        """
        Identify the proper folder to move the assembled folder into under WGSspades on the nas
        Then move the folder 
        """
        self.timelog.time_print("Moving files into the proper WGSSpades section on the nas.")
        assembly_done_dir = os.path.join(self.assembly_dir, self.ftp_server.folder_name + "_Assembled")

        # If local lab abbreviation it should be put in the local WGSspades folder
        if self.ftp_server.lab_name is "SEQ":
            wgs_dir = os.path.join(self.nas_mnt, "WGSspades", self.ftp_server.folder_name + "_Assembled")

        # If external lab abbreviation it should be put in the external WGSspades folder
        elif self.ftp_server.lab_name is not None:
            wgs_dir = os.path.join(self.nas_mnt, "External_WGSspades", self.ftp_server.lab_name,
                                   self.ftp_server.folder_name + "_Assembled")

        # If neither lab abbreviation it should be put in a dummy folder
        else:
            wgs_dir = os.path.join(self.nas_mnt, "External_WGSspades", 'na', self.ftp_server.folder_name)

        # Move the folders from the 'To_Assemble' directory into proper 'WGSSpades' directory
        self.copy_assembled_folder(assembly_done_dir, wgs_dir)
        return str(wgs_dir)

    def zip_wgsspades_files(self, wgs_dir):
        """
        Create the zip file that will be uploaded to the Redmine issue. It will contain the 'Reports' folders 
        from the results of the current run 
        :param wgs_dir: The WGSspades directory where the assembly result files can be located on the nas
        """
        # Folders to be zipped into the redmine results that will be uploaded
        folder_list = ["reports"]
        # Name of the zip file
        zip_file_name = self.ftp_server.folder_name + ".zip"

        zip_path = os.path.join(wgs_dir, zip_file_name)
        self.timelog.time_print("Creating zip file %s" % zip_path)

        if os.path.isdir(zip_path):
            shutil.rmtree(zip_path)

        # If for some reason the zip file already exists due to a re-run, delete the old one
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

        return zip_path

    @staticmethod
    def copy_assembled_folder(assembled_dir, wgs_dir):
        """
        Copies the assembled folder from the 'To_Assemble' section on the nas to the proper location in the WGSspades 
        section
        :param assembled_dir: Directory of the assembled folder in the 'To_Assemble' section on the nas
        :param wgs_dir: Directory in WGSspades where the folder should be moved to
        """

        # If the Directory already exists in WGSspades remove it and overwrite with the new information
        if os.path.isdir(wgs_dir):
            shutil.rmtree(wgs_dir)

        # Copy the assembled folder into the proper WGSSpades location on the nas
        copy_tree(assembled_dir, wgs_dir)
