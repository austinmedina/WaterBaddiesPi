import os
import time
import threading
from PIL import Image, ImageDraw, ImageFont
from gpiozero import LED, Button
from threading import Lock
from gpiozero import Device
import lgpio

try:
    displayhatmini.close()  # Release GPIO pins before reinitializing
except:
    pass  # Ignore if it wasn't initialized yet
from displayhatmini import DisplayHATMini

# source ~/Desktop/venv/bin/activate
# python /home/siymeare/Desktop/DisplayMotor/Updated_Display.py
# Initialize Display HAT Mini
class DisplayHat():
    
    def __init__(self, startMicroplasticDetection, startInorganicsMetalDetection, startArsenicDetection, startAll, restartBluetooth):
        self.width = DisplayHATMini.WIDTH
        self.height = DisplayHATMini.HEIGHT
        self.buffer = Image.new("RGB", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.buffer)

        self.displayhatmini = DisplayHATMini(self.buffer)
        self.displayhatmini.set_led(0.05, 0.05, 0.05)

        # Load fonts
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except:
            self.font = ImageFont.load_default()  # Fallback if font not found

        # Set up button hold actions (3-second hold time)
        self.displayhatmini.button_a.hold_time = 3  # Hold for 3 seconds before shutdown
        self.displayhatmini.button_b.hold_time = 3  # Hold for 3 seconds before reboot
        self.displayhatmini.button_x.hold_time = 3  # Hold for 3 seconds before reboot
        self.displayhatmini.button_y.hold_time = 3  # Hold for 3 seconds before reboot
        
        self.warning = False
        # Initializing Dark Mode
        self.switch = False
        self.mode_colorFont = "white"
        self.mode_background = "black"
        self.mode_timer = "blue"
        self.mode_percentage = "green"
        self.mode_warning = "red"
        
        # Timer and batch state
        self.counterStep = 0
        
        self.update_display()
        # Show initial screen
        self.counter_thread = threading.Thread(target=self.counter, daemon=True)
        self.counter_thread.start()
        # Run the button listener in a separate thread
        self.button_thread = threading.Thread(target=self.button_listener, args=(startMicroplasticDetection, startInorganicsMetalDetection, startArsenicDetection, startAll, restartBluetooth, None), daemon=True)
        self.button_thread.start()

    def toggle_dark(self):
        self.switch = not switch  # Toggle between 1 and -1
        if self.switch == False:
            self.mode_colorFont = "white"
            self.mode_background = "black"
            self.mode_timer = "blue"
            self.mode_percentage = "green"
            self.mode_warning = "red"
        else:
            self.mode_colorFont = "black"
            self.mode_background = "white"
            self.mode_timer = "navy"
            self.mode_percentage = "lime"
            self.mode_warning = "darkred"


    # ------------------ GUI Display Functions ------------------
    def update_display(self):
        """Redraws the screen with updated values."""

        self.draw = ImageDraw.Draw(self.buffer)  # Create drawing interface
        self.draw.rectangle((0, 0, self.width, self.height), fill=self.mode_background)  # Clear screen

        # Timer
        currentCounter = time.strftime("%H:%M:%S", time.gmtime(self.counterStep))
        self.draw.text((10, 10), f"Timer: {currentCounter}", font=self.font, fill=self.mode_timer)

        current_state = 1
        self.draw.text((10, 50), f"Stage:\n{current_state}", font=self.font, fill=self.mode_colorFont)

        # Completed State
        state_index=0
        completed_text = "Completed:\nNone"
        self.draw.text((10, 100), completed_text, font=self.font, fill=self.mode_colorFont)
        # Warning Message
        warning_text = "Warning:\nNone"
        self.draw.text((10, 150), warning_text, font=self.font, fill=self.mode_warning)
        # Percent Completed
        percent = int(78)
        self.draw.text((self.width - 60, self.height - 40), f"{percent}%", font=self.font, fill=self.mode_percentage)

        # Display the updated screen
        self.displayhatmini.display()


    def counter(self):
        """Updates the timer every second."""
        self.counterStep
        while True:
            self.counterStep += 1
            self.update_display()
            time.sleep(1)


    # Function to keep listening for button events
    def button_listener(self, microplastics, paperfluidics, arsenic, allStart, bluetoothReset, destroy=None):
        self.displayhatmini.button_a.when_pressed = microplastics
        self.displayhatmini.button_b.when_pressed = paperfluidics
        self.displayhatmini.button_x.when_pressed = bluetoothReset
        self.displayhatmini.button_y.when_pressed =self.toggle_dark
        
        self.displayhatmini.button_a.when_held = arsenic
        self.displayhatmini.button_b.when_held = allStart
        self.displayhatmini.button_x.when_held = lambda: os.system("sudo shutdown -h now")
        self.displayhatmini.button_y.when_held = lambda: os.system("sudo reboot now")

    def destroy(self):
        Device.close()
    
