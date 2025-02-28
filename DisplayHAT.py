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
width = DisplayHATMini.WIDTH
height = DisplayHATMini.HEIGHT
buffer = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(buffer)

displayhatmini = DisplayHATMini(buffer)
displayhatmini.set_led(0.05, 0.05, 0.05)

# Load fonts
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
except:
    font = ImageFont.load_default()  # Fallback if font not found

# Initialize button handling
button_a_press_start = None
button_b_press_start = None
# Set up button hold actions (3-second hold time)
displayhatmini.button_a.hold_time = 3  # Hold for 3 seconds before shutdown
displayhatmini.button_a.when_held = lambda: os.system("sudo shutdown -h now")

displayhatmini.button_b.hold_time = 3  # Hold for 3 seconds before reboot
displayhatmini.button_b.when_held = lambda: os.system("sudo reboot now")
warning = False
# Initializing Dark Mode
switch = False
mode_colorFont = "white"
mode_background = "black"
mode_timer = "blue"
mode_percentage = "green"
mode_warning = "red"


def toggle_switch():
    global switch, mode_colorFont, mode_background, mode_timer, mode_percentag, mode_warning  # Declare globals
    switch = not switch  # Toggle between 1 and -1
    print(f"Switch toggled: {switch}")  # Debugging print
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


# Timer and batch state
counterStep = 0


class BatchState:
    states = [
        'Dispatching Test Strips', 'Waiting for Reagents', 'Reagents Dispensed',
        'Analyzing Paperfluidics', 'Analyzing for Microplastics', 'Completed'
    ]


# ------------------ GUI Display Functions ------------------
def update_display():
    """Redraws the screen with updated values."""
    global counterStep

    draw = ImageDraw.Draw(buffer)  # Create drawing interface
    draw.rectangle((0, 0, width, height), fill=mode_background)  # Clear screen

    # Timer
    currentCounter = time.strftime("%H:%M:%S", time.gmtime(counterStep))
    draw.text((10, 10), f"Timer: {currentCounter}", font=font, fill=mode_timer)

    # Batch State
    state_index = min(counterStep // 10, len(BatchState.states) - 1)
    current_state = BatchState.states[state_index]
    draw.text((10, 50), f"Stage:\n{current_state}", font=font, fill=mode_colorFont)

    # Completed State
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
    global counterStep
    while True:
        counterStep += 1
        update_display()
        time.sleep(1)


# Function to keep listening for button events
def button_listener():
    displayhatmini.button_a.when_pressed = lambda: print("Power Button Pressed\n" + "Hold for 3 Seconds")
    displayhatmini.button_b.when_pressed = lambda: print("Reset Button Pressed\n" + "Hold for 3 Seconds")
    displayhatmini.button_x.when_pressed = lambda: print("Bluetooth Button Pressed")
    displayhatmini.button_y.when_pressed = lambda: print("Switch Display Pressed")
    displayhatmini.button_y.when_pressed = toggle_switch
    print("Press buttons on Display HAT Mini (Ctrl+C to exit)")
    while True:
        time.sleep(0.1)


# ------------------ Start Everything ------------------
update_display()  # Show initial screen
counter_thread = threading.Thread(target=counter, daemon=True)
counter_thread.start()
# Run the button listener in a separate thread
button_thread = threading.Thread(target=button_listener, daemon=True)
button_thread.start()
# Keep the script running
while True:
    time.sleep(1)
Device.close()
