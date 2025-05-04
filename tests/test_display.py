import os
import time
import threading
from PIL import Image, ImageDraw, ImageFont
from gpiozero import LED, Button
from threading import Lock
from gpiozero import Device
import lgpio
from queue import Queue

try:
    displayhatmini.close()  # Release GPIO pins before reinitializing
except:
    pass  # Ignore if it wasn't initialized yet
from displayhatmini import DisplayHATMini

# source ~/Desktop/venv/bin/activate
# python /home/siymeare/Desktop/DisplayMotor/Updated_Display.py
# Initialize Display HAT Mini
class DisplayHat():
    
    def __init__(self):
        self.width = DisplayHATMini.WIDTH
        self.height = DisplayHATMini.HEIGHT
        self.buffer = Image.new("RGB", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.buffer)

        self.displayhatmini = DisplayHATMini(self.buffer)
        self.displayhatmini.set_led(0.05, 0.05, 0.05)

        self.font = ImageFont.load_default()

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

        self.stage = ""
        self.warning = ""
        self.messageQueue = Queue()
        
        # Timer and batch state
        self.counterStep = 0
        
        self.counter_thread = threading.Thread(target=self.counter, daemon=True)
        self.counter_thread.start()
#         # Run the button listener in a separate thread
#         self.button_thread = threading.Thread(target=self.button_listener, daemon=True)
#         self.button_thread.start()

        self.displayhatmini.button_a.when_released = self.on_button_a_pressed
        self.displayhatmini.button_b.when_released = self.on_button_b_pressed
        self.displayhatmini.button_x.when_released = self.on_button_x_pressed
        self.displayhatmini.button_y.when_released = self.on_button_y_pressed
        
        self.displayhatmini.button_a.when_held = self.on_button_a_held
        self.displayhatmini.button_b.when_held = self.on_button_b_held
        self.displayhatmini.button_x.when_held = self.on_button_x_held
        self.displayhatmini.button_y.when_held = self.on_button_y_held

        self.messageThread = threading.Thread(target=self.updateText, daemon=True)
        self.messageThread.start()
        
        self.button_a_held = False
        self.button_b_held = False
        self.button_x_held = False
        self.button_y_held = False

    def toggle_dark(self):
        self.switch = not self.switch  # Toggle between 1 and -1
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

        # Current Stage
        stage_text = f"Stage:\n{self.stage}" if self.stage else "Stage:\nNot Started"
        self.draw.text((10, 50), stage_text, font=self.font, fill=self.mode_colorFont)

        # Warning Message
        warning_text = f"Warning:\n{self.warning}" if self.warning else "Warning:\nNone"
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

    def updateText(self):
        while True:
            try:
                texts = self.messageQueue.get()
                if ("stage" in texts):
                    self.stage = texts["stage"]
                if ("warning" in texts):
                    self.warning = texts["warning"]
                time.sleep(3)
                self.update_display()
            except:
                pass

    def updateQueue(self, text):
        self.messageQueue.put(text)

    # Function to keep listening for button events
#     def button_listener(self):
#     # Assign the functions to button events
#         self.displayhatmini.button_a.when_released = self.on_button_a_pressed
#         self.displayhatmini.button_b.when_released = self.on_button_b_pressed
#         self.displayhatmini.button_x.when_released = self.on_button_x_pressed
#         self.displayhatmini.button_y.when_released = self.on_button_y_pressed
#         
#         self.displayhatmini.button_a.when_held = self.on_button_a_held
#         self.displayhatmini.button_b.when_held = self.on_button_b_held
#         self.displayhatmini.button_x.when_held = self.on_button_x_held
#         self.displayhatmini.button_y.when_held = self.on_button_y_held

    def destroy(self):
        Device.close()
        
    def on_button_a_pressed(self):
        if not self.button_a_held:
            self.button_a_held = False
            print("Microplastics pressed")
            
        self.button_a_held = False

    def on_button_b_pressed(self):
        # Only trigger if not already pressed
        if not self.button_b_held:
            self.button_b_held = False
            print("Paperfluidics pressed")
            
        self.button_b_held = False

    def on_button_x_pressed(self):
        if not self.button_x_held:
            self.button_x_held = False
            print("Bluetooth Restart pressed")
            
        self.button_x_held = False      

    def on_button_y_pressed(self):
        if not self.button_y_held:
            self.button_y_held = False
            print("All start pressed")
            
        self.button_y_held = False      

    def on_button_a_held(self):
        print("Button A hold")
        self.button_a_held = True

    def on_button_b_held(self):
        print("Button B hold")
        self.button_b_held = True

    def on_button_x_held(self):
        print("Button X hold")
        self.button_x_held = True

    def on_button_y_held(self):
        print("Button Y hold")
        self.button_y_held = True  

if __name__ == "__main__":
    display = DisplayHat()
    
    while True:
        continue
