from picamera2 impote PiCamera2
from libcamera import controls

picam = Picamera2()
picam.start(show_preview=True)
picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
pcam.start_and_capture