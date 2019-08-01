"""*-----------------------------------------------------------------------*---
                                                         Author: Jason Ma
                                                         Date  : Jul 23 2019
                                      TODO

  File: display_worker.py
  Desc: TODO
---*-----------------------------------------------------------------------*"""


import cv2 as cv
import numpy as np
import os
import pickle
import socket
import struct
import sys
import threading
import time


import utils

class display_thread(threading.Thread):
  def __init__(self, conf, c_t=None):
    super(display_thread, self).__init__()
    self.running = True
    self.daemon = True
    self.images = None
    self.conf = conf
    self.c_t = c_t
    self.host="127.0.0.1"
    self.port=5000
    
    print("[disp] Thread initialized")

  def callback(self, msg):
    if msg == 'end':
      self.running = False

  def run(self):
    print("[disp] Thread started")

    #stop thread if not enabled
    if not self.conf.p["using_disp"]:
      print("[disp] NO DISP, ending thread")
      return
    
    #init images array for other threads to use
    self.images = []
    for i in range(self.conf.p["disp_cols"] * self.conf.p["disp_rows"]):
      self.images.append(np.zeros((self.conf.p["res_display"][0], self.conf.p["res_display"][1], 3), np.uint8))
    
    encode_param = [int(cv.IMWRITE_JPEG_QUALITY), 90]

    #start a server socket
    server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    print('Socket created')

    server.bind((self.host, self.port))
    print("[disp] socket bound: %s %d" % (self.host, self.port))
    server.listen(10)
    print("[disp] socket listening")

    while self.running:
      #send image to any clients
      try:
        client, addr = server.accept()
        print("[disp] client connected: %s" % (str(addr)))

        while True:
          #fast stream for camera capture
          if self.c_t.frame is not None:
            self.images[0] = self.c_t.frame

          #check for image validity
          invalid_image = False
          for img in self.images:
            if img is None:
              invalid_image = True

          if invalid_image:
            time.sleep(1)
            continue

          stacked_image = utils.stack_images(self.images, self.conf.p["res_display"], self.conf.p["disp_rows"], self.conf.p["disp_cols"])
          
          if stacked_image is None:
            continue

          _, frame = cv.imencode('.jpg', stacked_image, encode_param)
          data = pickle.dumps(frame, 0)
          size = len(data)

          time.sleep(1)
          
          client.sendall(struct.pack(">L", size) + data)
      except Exception as e:
        print("[disp] [error]", str(e))
            
    print("[disp] Thread stopped")
