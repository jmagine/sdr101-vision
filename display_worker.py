"""*-----------------------------------------------------------------------*---
                                                         Author: Jason Ma
                                                         Date  : Jul 23 2019
                                      TODO

  File: display_worker.py
  Desc: TODO
---*-----------------------------------------------------------------------*"""

import os
import threading
import cv2 as cv
import numpy as np
import time
import sys

import utils

class display_thread(threading.Thread):
  def __init__(self, conf, c_t=None):
    super(display_thread, self).__init__()
    self.running = True
    self.daemon = True
    self.images = None
    self.conf = conf
    self.c_t = c_t
    
    print("[disp] Thread initialized")

  def callback(self, msg):
    if msg == 'end':
      self.running = False

  def run(self):
    print("[disp] Thread started")

    self.images = []
    for i in range(self.conf.p["disp_cols"] * self.conf.p["disp_rows"]):
      self.images.append(np.zeros((16, 16, 3)))
    
    while self.running:
      
      #update images
      if self.c_t:
        self.images[0] = self.c_t.frame

      #check for image validity
      invalid_image = False
      for img in self.images:
        if img is None:
          invalid_image = True

      if invalid_image:
        time.sleep(1)
        continue

      #display images
      if self.conf.p["display_type"] != "no_disp":
        utils.display_stacked(self.images, self.conf.p["res_display"], self.conf.p["disp_rows"], self.conf.p["disp_cols"])
      
        #do not wait for input, but wait enough to display images
        # also holding q will usually allow the pi to quit
        if self.conf.p["display_type"] == "no_input":
          key = cv.waitKey(50)
          if key == ord('q'):
            print("[proc] Detected q, exiting")
            sys.exit(0)

        #wait for input from user, use space or arrow keys to advance/nav stream
        elif self.conf.p["display_type"] == "wasd_input":
          print("[proc] wasd")
          key = ''
          while True:
            key = cv.waitKey(1000)
            if key == ord('q'):
              print("[proc] Detected q, exiting")
              sys.exit(0)

            #left
            elif key == ord('a'):
              self.conf.p["read_pos"] -= 1
              break
            #right
            elif key == ord('d') or key == ord(' '):
              self.conf.p["read_pos"] += 1
              break
    print("[disp] Thread stopped")
