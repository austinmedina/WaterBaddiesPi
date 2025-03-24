import os
import time
from gpiozero import LED
from picamera2 import Picamera2
from libcamera import controls
from datetime import datetime

def test_picamera():
    os.makedirs("paperFluidicImages", exist_ok=True)
    picam = Picamera2()
    picam.configure(picam.create_still_configuration())
    picam.start()
    picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
    path = f'paperFluidicImages/{datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f")[:-3]}.png'
    picam.capture_file(path)
    picam.close()

    assert os.path.exists(path), f"File {path} was not created"

def test_with_leds():
    os.makedirs("paperFluidicImages", exist_ok=True)
    
    led = LED(21)
    led.on()
    time.sleep(0.5)

    picam = Picamera2()
    picam.configure(picam.create_still_configuration())
    picam.start()
    picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
    path = f'paperFluidicImages/{datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f")[:-3]}.png'
    picam.capture_file(path)
    picam.close()

    led.off()

    assert os.path.exists(path), f"File {path} was not created"
