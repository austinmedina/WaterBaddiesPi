from picamera2 import Picamera2
from libcamera import controls
from datetime import datetime


picam = Picamera2()
picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
picam.start_and_capture_file(f'plasticImages/{datetime.now().strftime("%F %T.%f")[:-3]}.png')