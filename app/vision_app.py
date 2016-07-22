import sys
sys.path.append("../include/")
import cv2 as cv
import numpy as np
import pydsm as dsm
import time

from picamera.array import PiRGBArray
from picamera import PiCamera
 
camera = PiCamera()
rawCapture = PiRGBArray(camera)

camera.sharpness = 0
camera.contrast = 0
camera.brightness = 50
camera.saturation = 0
camera.ISO = 0
camera.video_stabilization = False
camera.exposure_compensation = 0
camera.exposure_mode = 'auto'
camera.meter_mode = 'average'
camera.awb_mode = 'auto'
camera.image_effect = 'none'
camera.color_effects = None
camera.rotation = 0
camera.hflip = False
camera.vflip = False
camera.crop = (0.0, 0.0, 1.0, 1.0)

time.sleep(2)

while True:
    time.sleep(0.1)
    camera.capture(rawCapture, format="bgr")
    cv.imshow("Image", rawCapture.array)
    cv.waitKey(1)
    rawCapture.seek(0)
    rawCapture.truncate()
cv.destroyAllWindows()
