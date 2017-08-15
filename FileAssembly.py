import os
import time
import zipfile
from Utilities import UtilityMethods
from distutils.dir_util import copy_tree


class Assembly:

    def __init__(self, nas_mnt, timelog, all_files):
        self.nas_mnt = nas_mnt
        self.timelog = timelog
        self.all_files = all_files

        self.assembly_dir = os.path.join(self.nas_mnt, "To_Assemble")

    def create_symbolic_link(self, download_dir, folder_name):
        """
        Create a symbolic link for all files in the folder created on the nas to the "To_Assemble" folder
        The folder name is the same as the Inputted one from Redmine with the addition of "_Ready" on the end
        """
        download_dir = "/home/bownessn/Documents/Test_WGS/"

        assembly_ready_dir = os.path.join(self.assembly_dir, "Test_" + folder_name + "_Ready")

        if os.path.isdir(assembly_ready_dir):
            os.rmdir(assembly_ready_dir)
        UtilityMethods.create_dir(assembly_ready_dir)

        for files in self.all_files:
            # Path where the file is currently stored
            file_path = os.path.join(download_dir, files)
            # Path where the symbolic link is to be put
            dest_path = os.path.join(assembly_ready_dir, files)

            # create a symbolic link from the current file directory to into the To_Assemble folder
            os.symlink(file_path, dest_path)

    def wait_for_assembly(self, folder_name):

        counter = 0
        assembly_done_dir = os.path.join(self.assembly_dir, "Test_" + folder_name + "_Assembled")

        # wait a total of 18 * 10 minutes = 180 minutes
        while counter < 18:
            if os.path.isdir(assembly_done_dir):
                # if the assembly process has completed, continue with the process
                return True
            # if the assembly process has not completed wait 10 minutes before another check
            counter += 1
            time.sleep(600)

        return False

    def move_to_wgsspades(self, folder_name, lab_name):
        """
        Move the completed assembly folder into the proper folder in WGSSpades on the nas
        :return: 
        """

        assembly_done_dir = os.path.join(self.assembly_dir, "Test_" + folder_name + "_Assembled")
        wgs_dir = None

        if lab_name is "SEQ":
            wgs_dir = os.path.join(self.nas_mnt, "WGSspades", "Test_" + folder_name + "_Assembled")
        else:
            wgs_dir = os.path.join(self.nas_mnt, "External_WGSSpades", lab_name, "Test_" + folder_name + "_Assembled")

        if wgs_dir is None:
            wgs_dir = os.path.join(self.nas_mnt, "External_WGSSpades", 'na', folder_name)

        self.copy_assembled_folder(assembly_done_dir, wgs_dir)
        msg = str(wgs_dir)

        return msg

    @staticmethod
    def copy_assembled_folder(assembled_dir, wgs_dir):

        # if the Directory already exists in WGSSpades remove it and overwrite with the new information
        if os.path.isdir(wgs_dir):
            os.rmdir(wgs_dir)

        # Copy the assembled folder into the proper WGSSpades location on the nas
        copy_tree(assembled_dir, wgs_dir)

    def zip_wgsspades_files(self, folder_name, wgs_dir):
        """
        Zip the specified files including - Best Assemblies, Reports - and add the zip file to the folder
        :return: the path of the zip file
        """
        folder_list = ["BestAssemblies", "reports"]

        zip_path = os.path.join(wgs_dir, folder_name + ".zip")
        self.timelog.time_print("Creating zip file %s" % zip_path)

        if os.path.isdir(zip_path):
            os.rmdir(zip_path)

        zip_file = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
        for folder in folder_list:
            try:
                zip_file.write(os.path.join(wgs_dir, folder), arcname=folder)
                self.timelog.time_print("Files in: %s - added to the zip file." % folder)
            except FileNotFoundError:
                self.timelog.time_print("[Warning] Can't find %s, will leave it out of .zip" % folder)
                raise
        zip_file.close()

        return zip_path

