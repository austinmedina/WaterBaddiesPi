from picamera2 import PiCamera2
from libcamera import controls
from datetime import datetime


picam = Picamera2()
picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
picam.start_and_capture(f'plasticImages/{datetime.now().strftime("%F %T.%f")[:-3]}.png')