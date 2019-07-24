# ForwardVision

## Requirements
* Python 3.4+
* OpenCV 3.4.2+ (tested on 4.1.0)
* Numpy

## Optional Dependencies
* Pydsm (https://github.com/rahulsalvi/DistributedSharedMemory)

## Features
* Safely handles picamera or file stream
* Runs YOLOv3-tiny detector from OpenCV
* Feeds detections into DSM if enabled

## Goals
Detect mission objectives in the water to advise mission module where vehicle
is in relation to task. This includes PVC gates, buoys, path markers, and bins.

## Install ForwardVision
* `git clone https://github.com/sdrobotics101/vision.git`
* `cd vision`
* `python3 main.py` or `start.sh`

## Run the vision application
* Check config.cfg and modify as necessary
* `python3 main.py` or `start.sh`

## How to set up forward vision pi
* Start with Raspbian Buster or latest Raspbian
* `sudo hostname forward`
* `sudo vim /etc/hosts` 
    * Add definitions for this and other active pis
    * 127.0.0.1 forward
    * 10.0.0.42 master
    * 10.0.0.43 sensor
    * 10.0.0.44 navigation
    * 10.0.0.45 forward
    * 10.0.0.46 downward
    * 10.0.0.47 sonar
* sudo vim /etc/dhcpcd.conf
    * Add static eth0 configuration pointing to 10.0.0.45
    * If running on pi with Wi-Fi (RPi 3+), add router at 10.0.1.1 and add entries at /etc/wpa_supplicant/wpa_supplicant.conf
* `sudo raspi-config`
    * Expand filesystem
    * Enable camera
* `sudo apt-get update`
* `sudo apt-get install python3-pip` 
* `sudo pip3 install numpy`
* `sudo pip3 install picamera`
* `Get optimized OpenCV debs and install using`
* `sudo dpkg -i [latest_opencv].deb`
