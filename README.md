# WaterBaddiesPi

A Raspberry Pi–based embedded application for the Water Baddies Detection System, providing automated sensing, actuation, display, and Bluetooth communication.

---

## Table of Contents

1. [Overview](#overview)  
2. [Prerequisites](#prerequisites)  
3. [Hardware Configuration](#hardware-configuration)  
4. [Software Setup](#software-setup)  
   - [Install System Dependencies](#install-system-dependencies)  
   - [GPIO Pin Configuration](#gpio-pin-configuration)  
   - [Python Virtual Environment](#python-virtual-environment)  
5. [Systemd Service](#systemd-service)  
   - [Create the Service Unit](#create-the-service-unit)  
   - [Enable and Manage the Service](#enable-and-manage-the-service)  
6. [Usage](#usage)  
7. [Repository Structure](#repository-structure)  
8. [Testing](#testing)  
9. [Contributing](#contributing)  
10. [License](#license)  

---

## Overview

The WaterBaddiesPi repository contains everything needed to deploy the Water Baddies Detection System on a Raspberry Pi. It handles:

- GPIO control of motors, IR breakbeam sensors, buttons, and LEDs  
- Display initialization and screen updates  
- Bluetooth GATT service and communication  
- Image analysis for microplastics and colorimetric assays  
- Robust error handling and automatic restart

  ![System Diagram](./April%202025%20Software%20Architecture%20Diagram.png)
---

## Prerequisites

- **Hardware**: Raspberry Pi 3/4/5 with camera, IR sensors, motors, buttons, LEDs, and Display HAT  
- **OS**: Raspberry Pi OS (32-bit or 64-bit)  
- **Network**: Internet access for package installation  

---

## Hardware Configuration

Ensure the following GPIO pins are freed up on your Pi:

1. **GPIO 0 & GPIO 1**  
2. **GPIO 8**  

Edit `/boot/firmware/config.txt` and add the following lines (each code fence must be on its own lines):

```ini
# Disable Bluetooth to free GPIO0 & GPIO1
dtoverlay=disable-bt

# Turn off SPI to free GPIO8 if not used by other peripherals
dtparam=spi=off
```

Reboot the Pi for changes to take effect:

```bash
sudo reboot
```

---

## Software Setup

### Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip libdbus-1-dev
```

### GPIO Pin Configuration

Ensure any default assignments on GPIO 0, 1, and 8 are disabled as shown above.

### Python Virtual Environment

The `wbe/` directory is the virtual enviroment for the Water Baddies Detection System. We included the virtual enviroment because we had to modify some of the contents of the packages due to them being outdated. The library for the Display Hat Mini is the main one we modified so be aware when ubdatig through pip that the library may be overwritten.

---

## systemd Service

We use a systemd service to launch the application at boot.

### Create the Service Unit

```bash
sudo nano /etc/systemd/system/waterBaddies.service
```

Paste the following:
```ini
[Unit]
Description=Water Baddies Detection Service
After=network.target

[Service]
User=pi
Group=pi
WorkingDirectory=/home/pi/waterBaddies
ExecStart=/bin/bash -c "source /home/pi/waterBaddies/venv/bin/activate && python3 /home/pi/waterBaddies/systemWrapper.py"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Make the main script executable:
```bash
chmod +x ~/waterBaddies/systemWrapper.py
```

### Enable and Manage the Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable waterBaddies.service
sudo systemctl start  waterBaddies.service
```

- **Start:** `sudo systemctl start  waterBaddies.service`  
- **Stop:**  `sudo systemctl stop   waterBaddies.service`  
- **Status:**`sudo systemctl status waterBaddies.service`  

---

## Usage

Once the service is running, the Pi will:

1. Initialize GPIO interfaces (motors, sensors, LEDs)  
2. Bring up the Display HAT UI  
3. Advertise and handle Bluetooth GATT requests  
4. Listen for input from the Display and then run motors, check sensors, and analyze images as necessary 

---

## Repository Structure

```
.
├── bluetoothCreation/
│   └── baddiesDetection.py   # GATT service & advertisement
├── DisplayHAT.py             # Display init, drawing & button handlers
├── breakpointSensor.py       # IRSensor class for breakbeam detection
├── microscope_analysis.py    # Microplastics fluorescence analysis
├── paperfluidics_analysis.py # Colorimetric assay processing
├── systemWrapper.py          # Main application logic & error handling
├── venv/                     # Included Python virtual environment
└── requirements.txt          # Python dependencies
```

---

## Testing

- **findMicroscope.py**: Auto-detect camera index  
- **microscopeTest.py**: Capture & verify an image  
- **testBreakpoint.py**: Validate each IRSensor output  
- **test_doorButtons.py**: Monitor door button presses  
- **test_motor_breakpoint.py**: Cycle motors to their breakpoints  
- **tests/test_picamera.py**: LED-triggered picamera capture  
- **tests/test_motor.py**: Sequential motor activation  

Run tests inside the venv:
```bash
source venv/bin/activate
python or pytest
```
