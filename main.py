import cv2
from numpy import array as nparray
from shutil import copyfile, copyfileobj
from json import load, dump, dumps
from socket import gethostbyname
from io import BytesIO, StringIO
from uuid import uuid1
from rmlines import RMLines
from paramiko import SSHClient
from scp import SCPClient
from sys import argv
from pdfreader import SimplePDFViewer, PageDoesNotExist

# EDIT THESE
notebook_uuid = "your_uuid" # UUID found using the "find_uuid.py" script
password = "your_password" # Edit this to be your remarkable's ssh password

image_full = nparray([])

# If the image is a .pdf it must first be processed
if (argv[1] in [".pdf", ".PDF"]):
  # Extract images in the pdf and save them in the images array
  images = []
  with open(argv[1], "rb") as f:
    viewer = SimplePDFViewer(f)
    try:
        while True:
            viewer.render()
            images.extend(viewer.canvas.inline_images)
            images.extend(viewer.canvas.images.values())
            viewer.next()
    except PageDoesNotExist:
        pass
  images[0].to_Pillow().save("converted.png")
  # Load the image
  image_full = cv2.imread("converted.png")
# Otherwise, the image can be loaded directly using open cv
else: 
  image_full = cv2.imread(argv[1])

# Downscale the image so that it fits on the remarkable's screen (with some buffer room for selecting)
# Find the largest of the two dimensions
width = 0
height = 0
image = nparray([])

# The length of the largest dimension of the image
target_length = 1000 # in px

# Height is larger
ratio = image_full.shape[1] / image_full.shape[0]
if (image_full.shape[0] > image_full.shape[1]):
  # Resize the height, calculate the width from the new ration
  image = cv2.resize(image_full, (round(ratio * target_length), target_length))

# Either the same size or of the width is larger
else:
    image = cv2.resize(image_full, (target_length, round((1 / ratio) * target_length)))

# Convert the image to greyscale 
grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Blur the image slightly
#blurred_image = cv2.GaussianBlur(grayscale_image, (3,3), 3)
blurred_image = grayscale_image
# Get the edges of the image with canny edge detection
edges_image = cv2.Canny(blurred_image, 25, 75)

# Dilate the image
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,1))
#dilated_edges = cv2.dilate(edges_image, kernel)
dilated_edges = edges_image

# Extract the contours from the canny filtered binary image
contours, hierarchy = cv2.findContours(dilated_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# Convert the contours given by opencv to an SVG in memory
svg_buffer = StringIO()
svg_buffer.write(f'<svg xmlns="http://www.w3.org/2000/svg">')
for c in contours:
    svg_buffer.write('<path d="M')
    for i in range(len(c)):
        x, y = c[i][0]
        svg_buffer.write(f"{x} {y} ")
    svg_buffer.write('"></path>')
svg_buffer.write("</svg>")
svg_buffer.seek(0)

# Convert SVG to rm lines
rm_lines_buffer = BytesIO()
lines_file = RMLines.from_svg(svg_buffer)
lines_file.to_bytes(rm_lines_buffer)

# Look up the remarkable's IP from its hostname
ip_address = gethostbyname("remarkable.local")

# Establish a connection to the remarkable
with SSHClient() as ssh:
    ssh.load_system_host_keys()
    ssh.connect(ip_address, 22, "root", password)

    # Start SCP
    with SCPClient(ssh.get_transport()) as scp:

      # Generate a new UUID for the page
      page_uuid = str(uuid1());

      # Push the page to the circuit scans notebook
      remarkable_files_dir = "~/.local/share/remarkable/xochitl/"
      rm_lines_buffer.seek(0)
      scp.putfo(rm_lines_buffer, remarkable_files_dir + notebook_uuid + "/" + page_uuid + ".rm")

      # Append "Blank" on a new line to the notebook's .pagedata file
      # First step is to read in the current .pagedata file. Unfortunately the SCP module
      # only allows for files obtained with .get() to be stored on the file system. So, 
      # we write content to a temp file
      pagedata_temp_file_name = "temp.pagedata"
      scp.get(remarkable_files_dir + notebook_uuid + ".pagedata", "./" + pagedata_temp_file_name)

      # With the file loaded, we open it in append mode to add a new "Blank"
      with open("./" + pagedata_temp_file_name, "a") as f:
        f.write("Blank\n")

      # Now we can copy this file back to the remarkable
      scp.put("./" + pagedata_temp_file_name, remarkable_files_dir + notebook_uuid + ".pagedata")
      
      # Next the .content JSON file of the notebook needs to be modified. It has a pages array which stores
      # the uuids of each page. It also has a page count variable that needs to be incremented. The process
      # is similar to that used for the .pagedata file, except the content of the .content file will be 
      # JSON parsed

      # Get the notebook's .content file and store it temporarily
      content_temp_file_name = "temp.content"
      scp.get(remarkable_files_dir + notebook_uuid + ".content", "./" + content_temp_file_name)
     
      # Open the file in read mode
      content_file_json = {}
      with open("./" + content_temp_file_name, "r+") as f:
        # Parse the file as JSON
        content_file_json = load(f);

        # Append to the pages array the uuid of the new page
        content_file_json["pages"].append(page_uuid);

        # Increment the pageCount variable
        content_file_json["pageCount"] = content_file_json["pageCount"] + 1;

      # Write the updated JSON to the file
      with open("./" + content_temp_file_name, "w") as f:
        f.write(dumps(content_file_json))

      # Copy the file back to the remarkable
      scp.put("./" + content_temp_file_name, remarkable_files_dir + notebook_uuid + ".content");
     
      # The -metadata.json file is a per-page file. It describes the name of the layer on each page. 
      # For our purposes we can just push a generic copy with ony layer named "Layer 1"
      
      # Create the JSON object
      metadata_file_json = {
        "layers": [
          {
            "name": "Layer 1"
          }
        ]
      }

      # Convert it to a buffer
      metadata_file_buffer = StringIO()
      dump(metadata_file_json, metadata_file_buffer)
      metadata_file_buffer.seek(0)
      scp.putfo(metadata_file_buffer, remarkable_files_dir + notebook_uuid + "/" + page_uuid + "-metadata.json")
    # Once the files are sent the remarkable's xochitl service needs to be restarted to force
    # a document scan. This is done via sending a command over ssh
    ssh.exec_command("systemctl restart xochitl")


      