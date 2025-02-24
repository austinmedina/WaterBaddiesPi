from picamera2 import Picamera2
from libcamera import controls
from datetime import datetime

def capturePiImage():
    picam = Picamera2()
    picam.configure(picam.create_still_configuration()) # Add this line
    picam.start()
    picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
    path = f'paperFluidicImages/{datetime.now().strftime("%Y-%m-%d-%H-%M-%S.%f")[:-3]}.png'
    picam.capture_file(path)
    picam.close()
    return path

print(capturePiImage())