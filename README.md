## WGSAssembly
Automated download and run of "the pipeline" on a specified folder from the ftp server, with automatic uploaded results.

#### How to Run? 
Create a Redmine issue with the Subject as "WGS Assembly" 
- upper/lower case letters do not matter
- correct spelling and spacing is important

In the description of the issue, specify only the folder that appears on the ftp server (incoming/cfia-ak/"your_folder")
with all the proper files.

Once the WGS Assembly process has completed, the author will have the issue updated back to them with the results of 
the run attached to the Redmine issue. If an error occurs the author of the issue will be notified.

------- For more in depth instructions please see the documentation at - RedmineAutomationDocs - where a graphical 
explanation is given on the usage. -------

## Components - How it Works

The WGS Assembly uses the base GenericRedmineAutomator and customizes it to download files from the ftp server, 
to their proper location in the 'MiSeq_Backup' folders on the server. The files are then moved to the 'To_Assemble'
folder where the pipeline is run. Once the pipeline has completed, the results are stored in the proper 
'WGSspades' folder. Finally the results are uploaded back to the author on Redmine and on the FTP.

#### respond_to_issue(self, issue)
This method is from the GenericRedmineAutomator and takes an individual issue from Redmine, with all of its base 
information (i.e. Description, Topic...). It will then update the author on Redmine that the task is in progress and 
will run a series of operations needed to complete the WGS Assembly Process. The process entails 5 main portions
which executed in order: 

#### FTP - ServerInfo
The ServerInfo object is used to store variables that can be passed through to all the different ftp processes used. It 
is created first and it contains:
- ftp username, ftp password
- folder_name - Folder specified on the ftp server
- all_files - All file names on the ftp server in the specified folder
- destinationurl - Url used to access the files on the ftp server with pycurl
- lab_name - Lab abbreviation name used when storing data in the correct places


#### FTP - Download
The Download class takes the ServerInfo object as input and uses pycurl to download files from the ftp server 
into specified locations on the nas. 

This class is used to Download the sample sheet from the ftp as the first step. Then if the files are validated 
it will be called again to download the remaining files into the proper 'MiSeq_Backup' folder.


#### FTP - Validation
The Validation class takes the ServerInfo object as input; it uses the downloaded SampleSheet 
(from the specified folder) as reference for which files should be contained within that same folder.


If there are 2 files associated with each sequence given on the SampleSheet then the upload is validated and the 
remainder of the steps may occur. 
If there is not 2 files associated with a sample on the SampleSheet, the author will be updated as to which files are 
missing a pair. The author must remedy this and create a new issue with the proper files/samplesheet.


#### File Assembly
Once the files have been validated, they must be manipulated through the nas so the pipeline can be run and for the 
files to be stored correctly. The files are moved in the following steps: 

- Symbolic links are created from the files in the 'MiSeq_Backup' location to the 'To_Assembled' folder. The new folder 
is marked with the _Ready flag so the pipeline can pick it up
- A waiting process for a maximum of 6 hours (could be changed to more) is the started. The code is looking for 
the folder with the same name but a _Assembled flag instead of _Ready
- Once the _Assembled flag is found, the "yourfolder_Assembled" folder will be moved to the proper 'WGSspades' directory 
where the output of the pipeline run will be stored
- Finally the 'Results' folder created from the pipeline run will be zipped so that it can be uploaded back to the
 issue on Redmine later

## Results 

Once the pipeline run has been completed and the results have been stored in the proper 'WGSspades' folder. The 
'results' folder from the run is zipped and uploaded to the Redmine issue with the name "your_folder_results.zip". The 
author will then be notified that the process has completed. 

However the 'Best Assemblies' folder should be shared as well, but is too large to store in quantities on Redmine. 
So both it and "Results" folder should be zipped and uploaded to the ftp server in the directory 
"/outgoing/cfia-ak/your_folder_ftp_results.zip"

#### FTP Upload
Once the pipeline has been completed and the files stored correctly as stated above. This class will zip together the 
"Best Assemblies" and "Reports" folders. 

This folder should then be uploaded to the ftp server in - "/outgoing/cfia-ak/your_folder_ftp_results.zip"
(The code to upload the zip file to the ftp server has not been finished)


