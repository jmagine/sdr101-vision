# ForwardVision

## Requirements
* Python 3.4+
* OpenCV 3.1.0
* Numpy
* PyDSM

## Features
* Safely handles picamera
* Reads goals from master DSM buffer

## Goals
Detect mission objectives in the water to advise mission module where vehicle
is in relation to task. This includes PVC gates, buoys, and shaped cutouts.

## Upcoming
* Use alternate colorspace to threshold better
* Communicate with PyDSM
* Move code to C++
* FPGA Acceleration 

## Install ForwardVision
* `git clone git@github.com:sdrobotics101/forward-vision.git`
* `cd ForwardVision`
* `pip3 install -e .`

## Run the vision application
* `python3 vision_app.py` 

## How to set up forward vision pi
* Start with Raspbian
* Set hostname to `forward`
* Set IP to `10.0.0.45`
* `sudo raspi-config`
    * Expand filesystem
* `sudo apt-get update`
* `sudo apt-get install`
* `sudo raspi-update`
* `sudo apt-get install build-essential cmake pkg-config libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libgtk2.0-dev libatlas-base-dev gfortran`
* `wget https://bootstrap.pypa.io/get-pip.py`
* `sudo python3 get-pip.py` 
* `sudo pip3 install numpy`
* `wget "https://github.com/jabelone/OpenCV-for-Pi/raw/master/latest-OpenCV.deb"`
* `sudo dpkg -i latest-OpenCV.deb`
    * Prebuilt OpenCV 3.1.0 binaries
* `sudo pip3 install picamera`
