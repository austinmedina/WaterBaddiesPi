# WaterBaddiesPi
Welcome to the Embedded Code for the Water Baddies Detection System!

The following repository includes everything you need to have quickly get the Water Baddies Detection System running

When setting up the raspberry pi for use there are a couple of specific things you must do. Some libraries will need to be installed on the pi using apt in order to use the dbus library. You will also have the modify the file boot/firmware/config.txt to free up gpio 0, 1, and 8 using the following:
~insert text here

The main application for the Water Baddies Detection System is the systemWrapper.py. This file contains a class called system which handles all of the GPIO communication with motors, IRSensors, buttons, and leds. The class also handles initializing the display, initializes the bluetooth and processing bluetooth communication, and handles any errors that occur during running of the system.

The systemWrapper.py is run whenver the raspberry pi initially starts up. We use a service called waterBaddies.service to do this. To create the service run:
sudo nano /etc/systemd/system/waterBaddies.service

Then add the following to the contents of the waterBaddies.service file:
[Unit]
Description=Water Baddies Service
After=network.target  # Start after the network is up

[Service]
User=pi  # Run as the 'pi' user (or your desired user)
Group=pi
WorkingDirectory=/home/pi/waterBaddies  # Set the working directory
ExecStart=/bin/bash -c "source /home/pi/waterBaddies/venv/bin/activate && python3 /home/pi/waterBaddies/systemWrapper.py"
#  * /bin/bash -c:  Execute a shell command
#  * source /home/pi/waterBaddies/venv/bin/activate: Activate the virtual environment.
#  * && :  And then...
#  * python3 /home/pi/waterBaddies/systemWrapper.py:  Run your Python script.
Restart=on-failure  # Restart the service if it crashes
RestartSec=5  # Wait 5 seconds before restarting

[Install]
WantedBy=multi-user.target  # Start at boot-up

Make it executable: chmod +x /home/pi/waterBaddies/systemWrapper.py

Finally enable the service:
sudo systemctl enable waterBaddies.service

Here are some quick commands for dealing with the service:
To start: sudo systmctl start waterBaddies.service
To Stop: sudo systemctl stop waterBaddies.service
To Check Status: sudo systemctl status waterBaddies.service

Important files:
systemWrapper.py: This is the main logic for the entire system and handles all of the logic for the system
DisplayHAT.py: Includes the initiliation fo the display, along with utility functions, button handling, and the logic to draw on the screen
breakpointSensor.py: Includes a class called IRSensor which is a used for the IRBreaksensors and includes a function to check if an object is detected
microscope_analysis.py: Includes the image analysis functions for finding floresced microplastics 
paperfluidics_analysis.py: Includes the image analysis for getting the color change of the test pads and mapping the color values to conecntrations
bluetoothCreation/baddiesDetection.py: Creates the GATT Bluetooth service for the Raspberry Pi, creates the advertisement for the service, and provides utility functions used in the system wrapper to update values and restart the service
wbe: This is the virtual enviroment the system runs on. We have included it in the repository because we have had to change some of the libraries due to them being outdated. So to allow for easy movement between raspberry pi's we have included the virtual envroment here.

Tests:
findMicroscope.py: Loops through all available ports to find the correct index the microscope is on
microscopeTest.py: Connects to the microscope, takes a photo, saves it, and asserts the file was saved
testBreakpoint.py: Checks each IRSensor to see if an object is detected. If the system was built correctly all IRSensors should return false
test_doorButtons.py: A while loops that will print true or false as the door buttons are pressed
test_motor_breakpoint.py: Will run the motors in the secquence they are fired in the actual system. Runs each motor until the desired breakpoint sensor is hit, meaning the cartirdge will be in the correct place for the water dropper or the camera.
tests/test_picamera.py: Takes a photo using the picamera when the LED is turned on and saved the image.
tests/test_motor.py: Will fire each motor sequentially
