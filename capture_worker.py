'''*-----------------------------------------------------------------------*---
                                                         Author: Jason Ma
                                                         Date  : Aug 01 2018
                                      TODO

  File Name  : capture_worker.py
  Description: TODO
---*-----------------------------------------------------------------------*'''

import os
import threading
import cv2
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
    print("[cap] Save dir generated")

  def callback(self, msg):
    if msg == 'end':
      self.end_thread = True      
        
  def run(self):
    print("[cap] Thread initialized")
    print("[cap] Save dir: " + self.image_full_dir)
    
    #publish the live directory for the processor to handle stream
    with open("live_dir.log", 'w') as f:
      f.write(self.image_full_dir + "\n")

    with PiCamera() as camera:
      camera.resolution = self.image_size
      camera.framerate = 30

      #wait for auto gain control to settle
      #time.sleep(2)
      
      #camera.sharpness = 0
      #camera.contrast = 0
      #camera.brightness = 50
      #camera.saturation = 0
      #camera.ISO = 'auto'
      #camera.video_stabilization = False
      #camera.exposure_compensation = 0
      camera.exposure_mode = 'auto'
      camera.meter_mode = 'average'
      camera.awb_mode = 'auto'
      #camera.image_effect = 'none'
      #camera.color_effects = None
      camera.rotation = 0
      camera.hflip = False
      camera.vflip = False

      #camera.shutter_speed = camera.exposure_speed
      #camera.exposure_mode = 'off'

      #camera.iso = 200
      #camera.shutter_speed
      #g = camera.awb_gains
      #camera.awb_mode = 'off'
      #camera.shutter_speed = 0.125
      #g = camera.awb_gains
      #camera.awb_mode = 'off'
      #camera.awb_gains = g

      rawCapture = PiRGBArray(camera, size=self.image_size)
      time.sleep(5)
      
      print("[cap] Capture started")
      self.capture_started = True

      last_time = time.time()
      image_count = 0
      
      for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        curr_time = time.time()

        if curr_time - last_time < MIN_IMAGE_INTERVAL:
          rawCapture.truncate(0)
          continue

        if image_count % 10 == 0:
          print("[cap] Image count: %d\tInterval: %.5f\tImgDir: %s" % (image_count, curr_time - last_time, self.image_full_dir.split("/")[-1]))

        last_time = time.time()
        cv2.imwrite(os.path.join(self.image_full_dir, str(image_count) + ".jpg"), frame.array)
        rawCapture.truncate(0)
        image_count += 1

        if self.end_thread:
          print("[cap] Termination signal received from main thread")
          break
