'''*-----------------------------------------------------------------------*---
                                                         Author: Jason Ma
                                                         Date  : Aug 15 2018
                                 forward-vision

  File Name  : forward_vision.py
  Description: Main application for forward vision, looks for targets as
               specified by master module or manually specified. Can be placed
               in live mode for use with real robot, loopback mode to play back
               footage from mission and publish to DSM, or read mode to just
               run algorithms on previous missions
---*-----------------------------------------------------------------------*'''

import utils

import os
import re
import sys
import time

import cv2 as cv
import numpy as np

sys.path.append("/home/pi/python-shared-buffers/shared_buffers/")
from constants import *
from vision import Detection, DetectionArray
from serialization import *
from ctypes import sizeof
from master import *

'''[Global vars]------------------------------------------------------------'''

config_file = "config.cfg"
#color codes for opencv
#COLOR_RGB  = 1
#COLOR_GRAY = 0

#image shapes (width, height) for use with opencv
RES_1944 = (2592, 1944)
RES_1080 = (1920, 1080)
RES_720 = (960, 720)
RES_480 = (640, 480)
RES_240 = (320, 240)

'''[process_image]-------------------------------------------------------------
  Function to handle processing of image

  image - input image array
  
  max_x - most confident x coordinate
  max_y - most confident y coordinate
  confidence - confidence in range [0,255] for detection
----------------------------------------------------------------------------'''
def process_image(image, image_id=""):
  
  #[sanity checks]-------------------------------------------------------------
  if image is None:
    print("[proc] Image is None")
    sys.exit(1)
  
  #[preprocessing]-------------------------------------------------------------
  #resize images to low or mid res for faster processing
  #image = cv.resize(image, conf.p["res_process"], interpolation = cv.INTER_CUBIC)

  if not conf.p["rgb"]:
    image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

  #send images through darknet and publish to DSM
  if conf.p["using_darknet"]:
    blob = cv.dnn.blobFromImage(image, 1/255.0, conf.p["res_darknet"], [0,0,0], 1, crop=False)
    yolo.setInput(blob)
    out = yolo.forward(utils.get_output_names(yolo))
    utils.postprocess(image, out, conf_threshold=conf.p["darknet_conf_threshold"], nms_threshold=conf.p["darknet_nms_threshold"])
    t, _ = yolo.getPerfProfile()
    print("[yolo] cam_id: %s darknet_id: %5d time: %.2f" % (image_id, conf.p["darknet_id"], t / cv.getTickFrequency()))
    
    conf.p["darknet_id"] += 1

  #display images
  if conf.p["display_type"] != "no_disp":
    images = []
    images.append(image)
    utils.display_stacked(images, RES_240, 1, 1)
  
    #do not wait for input, but wait enough to display images
    # also holding q will usually allow the pi to quit
    if conf.p["display_type"] == "no_input":
      key = cv.waitKey(50)
      if key == ord('q'):
        print("[proc] Detected q, exiting")
        sys.exit(0)

    #wait for input from user, use space or arrow keys to advance/nav stream
    elif conf.p["display_type"] == "wasd_input":
      print("[proc] wasd")
      key = ''
      while True:
        key = cv.waitKey(1000)
        if key == ord('q'):
          print("[proc] Detected q, exiting")
          sys.exit(0)

        #left
        elif key == ord('a'):
          conf.p["read_pos"] -= 1
          break
        #right
        elif key == ord('d') or key == ord(' '):
          conf.p["read_pos"] += 1
          break

"""[pub_detections]------------------------------------------------------------
  Publishes detections to DSM
----------------------------------------------------------------------------"""
def pub_detections(client, boxes):
  #init everything to 0
  d_a = DetectionArray()
  for i in range(8):
    d_a.detections[i].cls = 255
    d_a.detections[i].x = 0
    d_a.detections[i].y = 0
    d_a.detections[i].w = 0
    d_a.detections[i].h = 0
    d_a.detections[i].size = 0

  #if detections exist, fill them in
  for i, b in enumerate(boxes):
    d = Detection()
    d.x = b[0]
    d.y = b[1]
    d.w = b[2]
    d.h = b[3]

    #TODO currently size is just height. set to w*h or remove in future
    d.size = b[3]
    
    #TODO handle class
    #cls = s[i].split(":")[0]
    #if "aswang" in cls:     d.cls = 0
    #elif "draugr" in cls:   d.cls = 1
    #elif "vetalas" in cls:  d.cls = 2
    #elif "jiangshi" in cls: d.cls = 3
    #elif "gate" in cls:     d.cls = 4
    #elif "bat" in cls:      d.cls = 5
    #elif "wolf" in cls:     d.cls = 6

    d_a.detections[i] = d
    print("[pub] c: %3d\tx: %.3f\ty: %.3f\tw: %.3f\th: %.3f" % (d.cls, d.x, d.y, d.w, d.h))
  
  client.setLocalBufferContents("forwarddetection", pack(d_a))

'''[main]----------------------------------------------------------------------
  
----------------------------------------------------------------------------'''
def main():
  print("[init] Mode: %s" % (conf.p["mode"]))

  #init dsm client and buffers
  if conf.p["using_dsm"]:
    print("[init] Initializing DSM client")
    client = pydsm.Client(conf.p["dsm_server_id"], conf.p["dsm_client_id"], True)

    print("[init] Initializing local buffers")
    client.registerLocalBuffer("forwarddetection", sizeof(DetectionArray), False)
    
    print("[init] DSM init complete")
  
  #init camera
  if conf.p["using_camera"]:
    print("[init] Camera init start")
    import capture_worker
    try:
      c_t = capture_worker.cap_thread(conf.p["res_capture"], conf.p["output_dir"])
      c_t.start()

      os.makedirs(os.path.join(c_t.image_full_dir, "darknet"))
    except Exception as e:
      print("[main] [error]: " + str(e))
    print("[init] Camera init complete")

  #main loop
  try:
    while True:
      #use frames from stream
      if conf.p["using_camera"]:
        image_list = os.listdir(c_t.image_full_dir)
        for img in image_list:
          if len(img.split(".")) < 2 or img.split(".")[1] != "jpg":
            image_list.remove(img)
        image_list.sort(key = lambda x: int(x.split(".")[0]), reverse=True)
        
        if len(image_list) < 2:
          print("[main] Stream not initialized yet, waiting")
          time.sleep(1)
          continue
        #note: can return empty frames before capture worker is fully init
        #print("[main] Pulling frame: %s" % (image_list[1]))
        image = c_t.frame
        image_id = image_list[1]

      #read image from input dir
      else:
        #find all images
        image_list = os.listdir(conf.p["input_dir"])
        for img in image_list:
          if len(img.split(".")) < 2 or img.split(".")[1] != "jpg":
            image_list.remove(img)
        image_list.sort(key = lambda x: int(x.split(".")[0]))
        
        #check validity of read_pos
        read_pos = conf.p["read_pos"]
        if read_pos < 0: conf.p["read_pos"] = 0
        if read_pos >= len(image_list): conf.p["read_pos"] = len(image_list) - 1
        
        image = utils.load_image(os.path.join(conf.p["input_dir"], str(image_list[read_pos])), conf.p["rgb"])
        image_name = image_list[read_pos]
      #handle processing and publishing
      process_image(image, image_id)
      
  except KeyboardInterrupt:
    print("[main] Ctrl + c detected, breaking")

#TODO merge with main init
"""[init]----------------------------------------------------------------------
  Parses config, initializes vision modules
----------------------------------------------------------------------------"""
conf = utils.Config()
conf.parse_conf("config.cfg")

#conditional imports which require integration with rest of system
if conf.p["using_dsm"]:
  sys.path.append("/home/pi/DistributedSharedMemory/")
  import pydsm

if conf.p["using_camera"]:
  from picamera.array import PiRGBArray
  from picamera import PiCamera

if conf.p["using_darknet"]:
  conf.p["darknet_id"] = 0

  classes = None
  with open(conf.p["darknet_names"], "rt") as f:
    classes = f.read().rstrip("\n").split("\n")
  
  yolo = cv.dnn.readNetFromDarknet(conf.p["darknet_cfg"], conf.p["darknet_weights"])
  
if __name__ == '__main__':
  main()
