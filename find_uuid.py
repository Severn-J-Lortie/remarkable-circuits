from socket import gethostbyname
from paramiko import SSHClient
from scp import SCPClient
from stat import S_ISDIR, S_ISREG
from json import load
from io import StringIO, BytesIO

# EDIT THIS
password = "your password"

# Find the IP Address of the remarkable
ip_address = gethostbyname("remarkable.local")

# Connect to the remarkable
with SSHClient() as ssh:
    ssh.load_system_host_keys()
    ssh.connect(ip_address, 22, "root", password)
      
    # Open the sftp client
    sftp = ssh.open_sftp();

    # List all directories and files
    remarkable_files_dir = "./.local/share/remarkable/xochitl/"
    target_notebook_name = "Circuit Schematics"
    for entry in sftp.listdir_attr(remarkable_files_dir):
      # Only look at files
      if (S_ISREG(entry.st_mode)):
        # Only look at .metadata files
        if (".metadata" in entry.filename): 
          # Create a file buffer
          metadata_buffer = BytesIO()

          # Read in file content
          sftp.getfo(remarkable_files_dir + entry.filename, metadata_buffer)

          # Convert the content of the file to JSON
          metadata_buffer.seek(0)
          metadata_file_json = load(metadata_buffer)

          # Extract the name
          notebook_name = metadata_file_json["visibleName"]

          # If the name matches the desired notebook name, print the uuid
          if (notebook_name == target_notebook_name):
            print("UUID of notebook with name: " + target_notebook_name + " is " + entry.filename)
        





