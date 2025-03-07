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
    
    def __init__(self):
        self.width = DisplayHATMini.WIDTH
        self.height = DisplayHATMini.HEIGHT
        self.buffer = Image.new("RGB", (width, height))
        self.draw = ImageDraw.Draw(buffer)

        self.displayhatmini = DisplayHATMini(buffer)
        self.displayhatmini.set_led(0.05, 0.05, 0.05)

        # Load fonts
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except:
            font = ImageFont.load_default()  # Fallback if font not found


        # Set up button hold actions (3-second hold time)
        self.displayhatmini.button_a.hold_time = 3  # Hold for 3 seconds before shutdown
        self.displayhatmini.button_b.hold_time = 3  # Hold for 3 seconds before reboot
        self.displayhatmini.button_x.hold_time = 3  # Hold for 3 seconds before reboot
        self.displayhatmini.button_y.hold_time = 3  # Hold for 3 seconds before reboot
        
        warning = False
        # Initializing Dark Mode
        switch = False
        mode_colorFont = "white"
        mode_background = "black"
        mode_timer = "blue"
        mode_percentage = "green"
        mode_warning = "red"
        
        # Timer and batch state
        self.counterStep = 0
        
        update_display()
          # Show initial screen
        self.counter_thread = threading.Thread(target=counter, daemon=True)
        self.counter_thread.start()
        # Run the button listener in a separate thread
        self.button_thread = threading.Thread(target=button_listener, daemon=True)
        self.button_thread.start()

    def toggle_dark(self):
        global switch, mode_colorFont, mode_background, mode_timer, mode_percentag, mode_warning  # Declare globals
        switch = not switch  # Toggle between 1 and -1
        if switch == False:
            mode_colorFont = "white"
            mode_background = "black"
            mode_timer = "blue"
            mode_percentage = "green"
            mode_warning = "red"
        else:
            mode_colorFont = "black"
            mode_background = "white"
            mode_timer = "navy"
            mode_percentage = "lime"
            mode_warning = "darkred"


    # ------------------ GUI Display Functions ------------------
    def update_display():
        """Redraws the screen with updated values."""

        draw = ImageDraw.Draw(buffer)  # Create drawing interface
        draw.rectangle((0, 0, width, height), fill=mode_background)  # Clear screen

        # Timer
        currentCounter = time.strftime("%H:%M:%S", time.gmtime(self.counterStep))
        draw.text((10, 10), f"Timer: {currentCounter}", font=font, fill=mode_timer)

        current_state = BatchState.states[state_index]
        draw.text((10, 50), f"Stage:\n{current_state}", font=font, fill=mode_colorFont)

        # Completed State
        state_index=0
        completed_text = "Completed:\nNone" if state_index == 0 else f"Completed:\n{BatchState.states[state_index - 1]}"
        draw.text((10, 100), completed_text, font=font, fill=mode_colorFont)
        # Warning Message
        warning_text = "Warning:\nNone" if warning == False else f"Warning:\n"  # add the warning message here, keep it short
        draw.text((10, 150), warning_text, font=font, fill=mode_warning)
        # Percent Completed
        percent = int((state_index / (len(BatchState.states) - 1)) * 100)
        draw.text((width - 60, height - 40), f"{percent}%", font=font, fill=mode_percentage)

        # Display the updated screen
        displayhatmini.display()


    def counter():
        """Updates the timer every second."""
        self.counterStep
        while True:
            self.counterStep += 1
            update_display()
            time.sleep(1)


    # Function to keep listening for button events
    def button_listener(self, microplastics, paperfluidics, arsenic, alll, bluetoothReset, destroy):
        displayhatmini.button_a.when_pressed = #Microplastics
        displayhatmini.button_b.when_pressed = #Papaerfluidics
        displayhatmini.button_x.when_pressed = lambda: print("Bluetooth Button Pressed") #bluetooothReset
        displayhatmini.button_y.when_pressed =self.toggle_dark
        
        self.displayhatmini.button_a.when_held = #Aresnic
        self.displayhatmini.button_b.when_held = #All
        self.displayhatmini.button_x.when_held = lambda: os.system("sudo shutdown -h now")
        self.displayhatmini.button_y.when_held = lambda: os.system("sudo reboot now")

    def destroy(self):
        Device.close()
    
