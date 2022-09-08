# Remarkable Circuits

Convert an image of a circuit schematic to an editable Remarkable 2 file. 

## How does it work?
The Python script first takes an image and performs thresholding and edge detection on it. Once the edges of the circuit are found, they are converted to an SVG format. Then, using the RMLines library, this svg is converted to the Remarkable's proprietary binary file format. This means the diagram is fully editable. Perfect for annotating or editing the circuit with your Remarkable 2! 

The script then takes the binary RMLines file and uploads it to your Remarkable via SSH.

## How do I set this up?

Prerequisites: A computer running MacOS, python, a remarkable and OneDrive (or other file sharing app). Make sure your computer is on and connected to the same network as the Remarkable. 

### On your Remarkable
- Create a notebook with the name "Circuit Scans"

### On your Mac
1. Create a folder in your base OneDrive (or other file sharing app's) directory and name it "Circuit Scans." Note: this *has* to be in the base of your OneDrive folder, not in any subdirectory.
2. Create a folder in your home directory called "remarkable_circuits_scripts" and place the python scripts there.
3. Open the main.py and find_uuid.py script and change the remarkable password there. Also change the notebook_uuid variable in the main.py script to the result of running the find_uuid.py script.
5. Simply install the included Automator action which monitors the Circuit Scans folder for changes and runs the remarkable_circuits script
6. Go on your phone, open OneDrive, scan and upload as many circuit photos as you want to the Circuit Scans folder. Watch as the script on your computer processes these, then sends them to your Remarkable over SSH. They will be in a notebook called "Circuit Scans."
