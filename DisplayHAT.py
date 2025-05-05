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
    
    def __init__(self, startMicroplasticDetection, startInorganicsMetalDetection, startAll, restartBluetooth, demo):
        self.width = DisplayHATMini.WIDTH
        self.height = DisplayHATMini.HEIGHT
        self.buffer = Image.new("RGB", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.buffer)

        self.displayhatmini = DisplayHATMini(self.buffer)
        self.displayhatmini.set_led(0.05, 0.05, 0.05)

        self.font = ImageFont.truetype('/usr/share/fonts/truetype/piboto/Piboto-Bold.ttf', 16)

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

        self._running = True
        self.plasticActive = False
        self.paperActive = False
        self.demoActive = False
        
        self.microplasticFunction = startMicroplasticDetection
        self.paperfluidicFunction = startInorganicsMetalDetection
        self.allStart = startAll
        self.bluetoothRestart = restartBluetooth
        self.demo = demo
        
        # Timer and batch state
        self.counterStep = 0
        self.percent = 0
        
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
        """Redraws the screen with updated, modern layout and wrapped text."""
        def wrap_text(text, font, max_width, draw):
            words = text.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                bbox = draw.textbbox((0, 0), test_line, font=font)
                if (bbox[2] - bbox[0]) <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            return lines

        self.draw = ImageDraw.Draw(self.buffer)
        self.draw.rectangle((0, 0, self.width, self.height), fill=self.mode_background)

        # Section dimensions
        header_height = 40
        footer_height = 40
        middle_top = header_height
        middle_bottom = self.height - footer_height
        mid_width = self.width // 2
        margin = 10

        # Header Section: Timer
        header_bg = getattr(self, 'mode_header', self.mode_background)
        self.draw.rectangle((0, 0, self.width, header_height), fill=header_bg)
        current_time = time.strftime("%H:%M:%S", time.gmtime(self.counterStep))
        self.draw.text((margin, 10), f"Timer: {current_time}", font=self.font, fill=self.mode_timer)

        # Middle Left: Stage Info with wrapped text
        stage_bg = getattr(self, 'mode_stage_bg', self.mode_background)
        self.draw.rectangle((0, middle_top, mid_width, middle_bottom), fill=stage_bg)
        stage_info = f"Stage: {self.stage}" if self.stage else "Stage: Ready"
        max_text_width = mid_width - (2 * margin)
        stage_lines = wrap_text(stage_info, self.font, max_text_width, self.draw)
        y_offset = middle_top + margin
        for line in stage_lines:
            self.draw.text((margin, y_offset), line, font=self.font, fill=self.mode_colorFont)
            bbox = self.draw.textbbox((0, 0), line, font=self.font)
            line_height = bbox[3] - bbox[1]
            y_offset += line_height + 2

        # Middle Right: Warning Message with wrapped text
        warning_bg = getattr(self, 'mode_warning_bg', self.mode_background)
        self.draw.rectangle((mid_width, middle_top, self.width, middle_bottom), fill=warning_bg)
        warning_msg = f"Warning: {self.warning}" if self.warning else "Warning: None"
        max_text_width = (self.width - mid_width) - (2 * margin)
        warning_lines = wrap_text(warning_msg, self.font, max_text_width, self.draw)
        y_offset = middle_top + margin
        for line in warning_lines:
            self.draw.text((mid_width + margin, y_offset), line, font=self.font, fill=self.mode_warning)
            bbox = self.draw.textbbox((0, 0), line, font=self.font)
            line_height = bbox[3] - bbox[1]
            y_offset += line_height + 2

        # Divider Lines
        divider_color = getattr(self, 'mode_divider', self.mode_colorFont)
        self.draw.line([(mid_width, middle_top), (mid_width, middle_bottom)], fill=divider_color, width=2)
        self.draw.line([(0, header_height), (self.width, header_height)], fill=divider_color, width=2)
        self.draw.line([(0, middle_bottom), (self.width, middle_bottom)], fill=divider_color, width=2)

        # Footer Section: Progress Bar for Percent Completed
        bar_left, bar_right = margin, self.width - margin
        bar_top, bar_bottom = self.height - footer_height + margin, self.height - margin
        full_bar_width = bar_right - bar_left
        progress_width = int(full_bar_width * (self.percent / 100))
        self.draw.rectangle((bar_left, bar_top, bar_right, bar_bottom), outline=divider_color, width=2)
        self.draw.rectangle((bar_left, bar_top, bar_left + progress_width, bar_bottom), fill=self.mode_percentage)
        percent_text = f"{self.percent}%"
        bbox = self.draw.textbbox((0, 0), percent_text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (self.width - text_width) // 2
        text_y = bar_top + ((bar_bottom - bar_top - text_height) // 2)
        self.draw.text((text_x, text_y), percent_text, font=self.font, fill=self.mode_background)

        self.displayhatmini.display()


    def updateText(self):
        while self._running:
            try:
                texts = self.messageQueue.get(block=False)
                if "stage" in texts:    self.stage   = texts["stage"]
                if "warning" in texts:  self.warning = texts["warning"]
            except:
                pass
            finally:
                self.counterStep += 1
                self.update_display()
                time.sleep(1)

    def updateQueue(self, text):
        self.messageQueue.put(text)
    
    def updatePercentage(self, perc):
        self.percent = perc

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
        print("Button B Pressed")
        if not self.button_b_held:
            if (not self.paperActive):
                self.button_b_held = False
                print("Paperfluidics pressed")
                self.paperActive = True
                self.paperfluidicFunction()
                print("paper closed")
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
            print("Demo pressed")
            if (not self.demoActive):
                self.demoActive = True
                self.demo()
            else:
                self.updateQueue({'warning': 'Demo already running'})
            
        self.button_y_held = False     

    def on_button_a_held(self):
        print("Button A hold")
        self.updateQueue({'warning': 'DESIGNED BY AUSTIN M, ALIA N, AIDAN T, DANNY K, JAMESON B, BRENDAN B, TYLER T'})
        self.button_a_held = True

    def on_button_b_held(self):
        print("Button B hold")
        self.button_b_held = True
        self.toggle_dark()

    def on_button_x_held(self):
        print("Button X hold")
        self.button_x_held = True
        os.system("sudo shutdown -h now")

    def on_button_y_held(self):
        print("Button Y hold")
        self.button_y_held = True
        self.bluetoothRestart()
        
    def updatePlasticActive(self, boo):
        self.plasticActive = boo
        
    def updatePaperActive(self, boo):
        self.paperActive = boo

    def getQueue():
        return self.messageQueue

    def setQueue(queue):
        self.messageQueue = queue

    def destory(self):
        # stop updateText loop
        self._running = False
        if self.messageThread.is_alive():
            self.messageThread.join(timeout=1)

        # unbind & close only the HAT’s buttons
        for btn in (
            self.displayhatmini.button_a,
            self.displayhatmini.button_b,
            self.displayhatmini.button_x,
            self.displayhatmini.button_y
        ):
            btn.when_released = btn.when_held = None
            btn.close()

        # close the HAT’s display/I2C interface
        try:
            self.displayhatmini.close()
        except:
            pass

        # drop reference so Python can GC it
        del self.displayhatmini
