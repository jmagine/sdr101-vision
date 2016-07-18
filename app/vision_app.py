import sys
sys.path.append("../include/")
import cv2 as cv
import numpy as np
import pydsm as dsm
import time

from picamera.array import PiRGBArray
from picamera import PiCamera
 
# initialize the camera and grab a reference to the raw camera capture

# allow the camera to warmup
time.sleep(1)
camera = PiCamera()
rawCapture = PiRGBArray(camera)
 
# grab an image from the camera
camera.capture(rawCapture, format="bgr")
image = rawCapture.array
 
# display the image on screen and wait for a keypress
cv.imshow("Image", image)
cv.waitKey(0)

