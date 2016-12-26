# ForwardVision
A forward vision system so bad, it should be illegal.

## Requirements
* Python 3.4+
* OpenCV 3.1.0
* Numpy
* PyDSM

## Goals
Ideally, we should be able to detect buoys and gates in the water.

## Upcoming
* Move code to C++
* FPGA Acceleration 

## Install ForwardVision
* `git clone git@gitlab.com:sdrobotics101/ForwardVision.git`
* `git submodule update --init --recursive`

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