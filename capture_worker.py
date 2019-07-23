'''*-----------------------------------------------------------------------*---
                                                         Author: Jason Ma
                                                         Date  : Aug 01 2018
                                      TODO

  File Name  : capture_worker.py
  Description: TODO
---*-----------------------------------------------------------------------*'''

import os
import threading
import cv2 as cv
import numpy as np
import time

from picamera.array import PiRGBArray
from picamera import PiCamera

import utils

#image shapes (width, height) for use with opencv
RES_1944 = (2592, 1944)
RES_1080 = (1920, 1080)
RES_720 = (960, 720)
RES_480 = (640, 480)
RES_240 = (320, 240)

MIN_IMAGE_INTERVAL = 0.1

class cap_thread(threading.Thread):
  def __init__(self, image_size, image_dir):
    super(cap_thread, self).__init__()
    self.end_thread = False
    self.daemon = True
    self.image_size = image_size
    self.image_dir = image_dir
    self.image_full_dir = utils.gen_dir(self.image_dir)
    self.capture_started = False

    self.camera = PiCamera()
    self.camera.resolution = self.image_size
    self.camera.framerate = 30
    self.raw_capture = PiRGBArray(self.camera, size=self.image_size)
    self.stream = self.camera.capture_continuous(self.raw_capture, format="bgr", use_video_port=True)
    
    self.frame = None
    
    #camera settings
    self.camera.exposure_mode = 'auto'
    self.camera.meter_mode = 'average'
    self.camera.awb_mode = 'auto'
    self.camera.rotation = 0
    self.camera.hflip = False
    self.camera.vflip = False

    print("[cap] Thread initialized")

  def callback(self, msg):
    if msg == 'end':
      self.end_thread = True      
        
  def run(self):
    
    #publish the live directory for the processor to handle stream
    with open("live_dir.log", 'w') as f:
      f.write(self.image_full_dir + "\n")

      print("[cap] Capture started")
      self.capture_started = True

      last_time = time.time()
      image_count = 0
      
      for f in self.stream:
        curr_time = time.time()
        self.frame = f.array
        
        if curr_time - last_time < MIN_IMAGE_INTERVAL:
          self.raw_capture.truncate(0)
          continue

        if image_count % 10 == 0:
          print("[cap] Image count: %d\tInterval: %.3f\tImgDir: %s" % (image_count, curr_time - last_time, self.image_full_dir.split("/")[-1]))

        last_time = time.time()
        cv.imwrite(os.path.join(self.image_full_dir, str(image_count) + ".jpg"), self.frame)
        self.raw_capture.truncate(0)
        image_count += 1

        if self.end_thread:
          print("[cap] Termination signal received from main thread")
          self.stream.close()
          self.raw_capture.close()
          self.camera.close()
          break
