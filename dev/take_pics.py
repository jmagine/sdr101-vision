'''*-----------------------------------------------------------------------*---
                                                         Author: Jason Ma
                                                         Date  : Jul 31 2018
                                      TODO

  File Name  : take_pics.py
  Description: TODO
---*-----------------------------------------------------------------------*'''

import os
import sys
import datetime
import time

import cv2

from picamera.array import PiRGBArray
from picamera import PiCamera

now = datetime.datetime.now()
print("Current time is: " + str(now))

now = str(now).split(".")[0]
now = now.replace(" ", "/")
now = now.replace(":", "_")

'''[Global Vars]------------------------------------------------------------'''

#location to save images
IMAGES_DIR = '/home/pi/ForwardVision/images/' + now + "/"

#width, height
IMAGE_SHAPE = (960, 720)

#time between images in seconds
MIN_IMAGE_INTERVAL = 1.0

'''[TODO]----------------------------------------------------------------------
  TODO
----------------------------------------------------------------------------'''
def main():
  
  print("[main] Creating directory at: " + IMAGES_DIR)

  if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)
  else:
    print("[main] Directory already exists. Exiting")
    sys.exit(1)

  with PiCamera() as camera:

    camera.resolution = IMAGE_SHAPE
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=IMAGE_SHAPE)
    
    time.sleep(0.5)
    
    print("[main] Capture starting")
    last_time = time.time()
    image_count = 0
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
      
      curr_time = time.time()
      if curr_time - last_time < MIN_IMAGE_INTERVAL:
        rawCapture.truncate(0)
        continue
      
      if image_count % 10 == 0:
        print("[main] Image count: " + str(image_count) + " Image interval: " + str(curr_time - last_time))

      last_time = time.time()

      cv2.imwrite(IMAGES_DIR + str(image_count) + '.jpg', frame.array)
      rawCapture.truncate(0)
      image_count += 1
      
if __name__ == '__main__':
  main()
