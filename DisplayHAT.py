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
    
    def __init__(self, startMicroplasticDetection, startInorganicsMetalDetection, startAll, restartBluetooth):
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
        
        self.button_a_held = False
        self.button_b_held = False
        self.button_x_held = False
        self.button_y_held = False

        self.plasticActive = False
        self.paperActive = False
        
        self.microplasticFunction = startMicroplasticDetection
        self.paperfluidicFunction = startInorganicsMetalDetection
        self.allStart = startAll
        self.bluetoothRestart = restartBluetooth
        
        # Timer and batch state
        self.counterStep = 0
        
        # Run the button listener in a separate thread
        self.button_thread = threading.Thread(target=self.button_listener, daemon=True)
        self.button_thread.start()

        self.messageThread = threading.Thread(target=self.updateText, daemon=True)
        self.messageThread.start()

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
        """Redraws the screen with updated, modern layout."""
        self.draw = ImageDraw.Draw(self.buffer)
        self.draw.rectangle((0, 0, self.width, self.height), fill=self.mode_background)

        # Section dimensions
        header_height = 40
        footer_height = 40
        middle_top = header_height
        middle_bottom = self.height - footer_height
        mid_width = self.width // 2

        # Header Section: Timer
        header_bg = getattr(self, 'mode_header', self.mode_background)
        self.draw.rectangle((0, 0, self.width, header_height), fill=header_bg)
        current_time = time.strftime("%H:%M:%S", time.gmtime(self.counterStep))
        self.draw.text((10, 10), f"Timer: {current_time}", font=self.font, fill=self.mode_timer)

        # Middle Left: Stage Info
        stage_bg = getattr(self, 'mode_stage_bg', self.mode_background)
        self.draw.rectangle((0, middle_top, mid_width, middle_bottom), fill=stage_bg)
        stage_text = f"Stage:\n{self.stage}" if self.stage else "Stage:\nNot Started"
        self.draw.text((10, middle_top + 10), stage_text, font=self.font, fill=self.mode_colorFont)

        # Middle Right: Warning Message
        warning_bg = getattr(self, 'mode_warning_bg', self.mode_background)
        self.draw.rectangle((mid_width, middle_top, self.width, middle_bottom), fill=warning_bg)
        warning_text = f"Warning:\n{self.warning}" if self.warning else "Warning:\nNone"
        self.draw.text((mid_width + 10, middle_top + 10), warning_text, font=self.font, fill=self.mode_warning)

        # Divider Lines
        divider_color = getattr(self, 'mode_divider', self.mode_colorFont)
        self.draw.line([(mid_width, middle_top), (mid_width, middle_bottom)], fill=divider_color, width=2)
        self.draw.line([(0, header_height), (self.width, header_height)], fill=divider_color, width=2)
        self.draw.line([(0, middle_bottom), (self.width, middle_bottom)], fill=divider_color, width=2)

        # Footer Section: Progress Bar for Percent Completed
        percent = 78  # Example percentage
        bar_left, bar_right = 10, self.width - 10
        bar_top, bar_bottom = self.height - footer_height + 10, self.height - 10
        full_bar_width = bar_right - bar_left
        progress_width = int(full_bar_width * (percent / 100))
        self.draw.rectangle((bar_left, bar_top, bar_right, bar_bottom), outline=divider_color, width=2)
        self.draw.rectangle((bar_left, bar_top, bar_left + progress_width, bar_bottom), fill=self.mode_percentage)
        percent_text = f"{percent}%"
        text_width, text_height = self.draw.textsize(percent_text, font=self.font)
        text_x = (self.width - text_width) // 2
        text_y = bar_top + ((bar_bottom - bar_top - text_height) // 2)
        self.draw.text((text_x, text_y), percent_text, font=self.font, fill=self.mode_background)

        self.displayhatmini.display()
      

    def updateText(self):
        while True:
            try:
                texts = self.messageQueue.get(block=False)
                if ("stage" in texts):
                    self.stage = texts["stage"]
                if ("warning" in texts):
                    self.warning = texts["warning"]
            except:
                pass
            finally:
                self.counterStep += 1
                self.update_display()
                time.sleep(1)

    def updateQueue(self, text):
        self.messageQueue.put(text)

    # Function to keep listening for button events
    def button_listener(self):
        self.displayhatmini.button_a.when_released = self.on_button_a_pressed
        self.displayhatmini.button_b.when_released = self.on_button_b_pressed
        self.displayhatmini.button_x.when_released = self.on_button_x_pressed
        self.displayhatmini.button_y.when_released = self.on_button_y_pressed
        
        self.displayhatmini.button_a.when_held = self.on_button_a_held
        self.displayhatmini.button_b.when_held = self.on_button_b_held
        self.displayhatmini.button_x.when_held = self.on_button_x_held
        self.displayhatmini.button_y.when_held = self.on_button_y_held

    def on_button_a_pressed(self):
        if not self.button_a_held:
            if (not self.plasticActive):
                self.button_a_held = False
                print("Microplastics pressed")
                self.plasticActive = True
                self.microplasticFunction()
            else:
                self.updateQueue({'warning': 'Cannot Start Microplastic As Its Currently Running'})
            
        self.button_a_held = False

    def on_button_b_pressed(self):
        if not self.button_b_held:
            if (not self.paperActive):
                self.button_b_held = False
                print("Paperfluidics pressed")
                self.paperActive = True
                self.paperfluidicFunction()
            else:
                self.updateQueue({'warning': 'Cannot Start Paperfluidics As Its Currently Running'})
            
        self.button_b_held = False

    def on_button_x_pressed(self):
        if not self.button_x_held:
            self.button_x_held = False
            print("All Start pressed")
            if (not self.paperActive and not self.plasticActive):
                self.paperActive = True
                self.plasticActive = True
                self.allStart()  
            elif (self.paperActive and not self.plasticActive):
                self.plasticActive = True
                self.microplasticFunction()
            elif (not self.paperActive and self.plasticActive):
                self.paperActive = True
                self.paperfluidicFunction()
            else:
                self.updateQueue({'warning': 'Both Paperfluidics and Microplastics already running'})
            
        self.button_x_held = False 

    def on_button_y_pressed(self):
        if not self.button_y_held:
            self.button_y_held = False
            print("Bluetooth pressed")
            self.bluetoothRestart()
            
        self.button_y_held = False     

    def on_button_a_held(self):
        print("Button A hold")
        self.button_a_held = True

    def on_button_b_held(self):
        print("Button B hold")
        self.button_b_held = True
        self.toggle_dark()

    def on_button_x_held(self):
        print("Button X hold")
        self.button_x_held = True
        #os.system("sudo shutdown -h now")

    def on_button_y_held(self):
        print("Button Y hold")
        self.button_y_held = True
        #os.system("sudo reboot now")

    def destroy(self):
        Device.close()
    
