import pycurl


class Upload:

    def __init__(self, ftp_server, issue, timelog):
        self.ftp_server = ftp_server

        self.username = ftp_server.username
        self.password = ftp_server.password
        self.folder_name = ftp_server.folder_name
        self.timelog = timelog

        self.uploadpath = 'ftp.agr.gc.ca/incoming/cfia-ak/' + self.folder_name

        # Create a URL that includes the user name and password, so PycURL can login to the FTP server
        self.destinationurl = 'ftp://{}:{}@{}'.format(self.username, self.password, self.uploadpath)

    def upload_zip_file(self, zip_path):

        # zip_path = "need to test this"

        curl = pycurl.Curl()

        curl.setopt(pycurl.URL, self.destinationurl+"/")
        curl.setopt(pycurl.FORM_CONTENTTYPE, "application/zip")

        with open(zip_path, 'r') as zip_file:
            curl.setopt(pycurl.UPLOAD, zip_file)

        curl.perform()
        curl.close()
