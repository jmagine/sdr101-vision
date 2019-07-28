'''*-----------------------------------------------------------------------*---
                                                         Author: Jason Ma
                                                         Date  : Aug 15 2018
                                    vision

  File Name  : main.py
  Description: Main application for vision module, looks for targets as
               specified by master module or manually specified. Submodule
               config located in config.cfg, including DSM, darknet, and cam.
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
def process_image(image, client, model_id=0, image_id=""):
  
  image_pred = None

  #[sanity checks]-------------------------------------------------------------
  if image is None:
    print("[proc] Image is None")
    return 0

  #[preprocessing]-------------------------------------------------------------
  #resize images to low or mid res for faster processing
  image = cv.resize(image, conf.p["res_process"], interpolation = cv.INTER_CUBIC)

  if not conf.p["rgb"]:
    image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

  #send images through darknet and publish to DSM
  if conf.p["using_darknet"]:
    blob = cv.dnn.blobFromImage(image, 1/255.0, conf.p["res_model"][model_id], [0,0,0], 1, crop=False)
    yolo[model_id].setInput(blob)
    out = yolo[model_id].forward(utils.get_output_names(yolo[model_id]))
    boxes = utils.postprocess(image, out, conf_threshold=conf.p["darknet_conf_threshold"], nms_threshold=conf.p["darknet_nms_threshold"])
    
    #use integer coords for drawing
    if conf.p["display_type"] != "no_disp":
      image_pred = utils.draw_preds(image, boxes, classes)
    
    #use normalized coords for dsm
    for box in boxes:
      box[0][0] = float(box[0][0] / conf.p["res_process"][0])
      box[0][1] = float(box[0][1] / conf.p["res_process"][1])
      box[0][2] = float(box[0][2] / conf.p["res_process"][0])
      box[0][3] = float(box[0][3] / conf.p["res_process"][1])
    
    t, _ = yolo[model_id].getPerfProfile()
    print("[yolo] res: %10s model_id: %d time: %.2f cam_id: %s pred_id: %5d.jpg" % (conf.p["res_model"][model_id], model_id, t / cv.getTickFrequency(), image_id, conf.p["darknet_id"]))
    
    #publish to dsm or print detections
    if conf.p["using_dsm"]:
      pub_detections(client, boxes)
    else:
      print_detections(boxes)
    
  return len(boxes), image_pred

"""[print_detections]----------------------------------------------------------
  Print deetections from YOLOv3
----------------------------------------------------------------------------"""
def print_detections(boxes):
  for b in boxes:
    cls = b[1][0]
    cnf = b[1][1]
    x = b[0][0] + b[0][2] / 2.0
    y = b[0][1] + b[0][3] / 2.0
    w = b[0][2]
    h = b[0][3]
    print("[det] | %7s %.2f |\txywh: %.2f %.2f %.2f %.2f" % (classes[cls], cnf, x, y, w, h))

"""[pub_detections]------------------------------------------------------------
  Publishes detections from YOLOv3 to DSM
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
    d.cls = int(b[1][0])
    d.cnf = b[1][1]
    d.x = float(b[0][0] + b[0][2] / 2.0)
    d.y = b[0][1] + b[0][3] / 2.0
    d.w = b[0][2]
    d.h = b[0][3]

    #TODO currently size is just height. set to w*h or remove in future
    d.size = b[0][3]
    
    d_a.detections[i] = d

    print("[pub] | %7s %.2f |\txywh: %.2f %.2f %.2f %.2f" % (classes[d.cls], d.cnf, d.x, d.y, d.w, d.h))
  
  client.setLocalBufferContents(conf.p["dsm_buffer_name"], pack(d_a))

'''[main]----------------------------------------------------------------------
  
----------------------------------------------------------------------------'''
def main():
  print("[init] Mode: %s" % (conf.p["mode"]))

  #init dsm client and buffers
  client = None
  if conf.p["using_dsm"]:
    print("[init] Initializing DSM client")
    client = pydsm.Client(conf.p["dsm_server_id"], conf.p["dsm_client_id"], True)

    print("[init] Initializing local buffers")
    client.registerLocalBuffer(conf.p["dsm_buffer_name"], sizeof(DetectionArray), False)
    
    print("[init] DSM init complete")
  #init camera
  if conf.p["using_camera"]:
    print("[init] Camera init start")
    try:
      c_t = capture_worker.cap_thread(conf.p["res_capture"], conf.p["output_dir"])
      c_t.start()

      os.makedirs(os.path.join(c_t.image_full_dir, "darknet"))
    except Exception as e:
      print("[main] [error]: " + str(e))
    print("[init] Camera init complete")
  
  if conf.p["display_type"] != "no_disp":
    d_t = display_worker.display_thread(conf, c_t)
    d_t.start()

  #main loop
  try:
    model_id = 0
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
        image_id = image_list[read_pos]

      #handle processing and publishing
      dets, image_pred = process_image(image, client, model_id, image_id)
      
      if conf.p["using_camera"]:
        cv.imwrite(os.path.join(c_t.image_full_dir, "darknet", str(conf.p["darknet_id"]) + ".jpg"), image_pred)
        conf.p["darknet_id"] += 1
      
      #update predictions on display
      if conf.p["display_type"] != "no_disp":
        d_t.images[1] = image_pred
        
      #adaptive resolution
      if dets == 0:
        model_id = min(model_id + 1, len(conf.p["model_cfgs"]) - 1)
      else:
        model_id = max(model_id - 1, 0)
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
  import capture_worker

if conf.p["display_type"] != "no_disp":
  import display_worker
  cv.namedWindow("[stacked]", cv.WINDOW_NORMAL)

if conf.p["using_darknet"]:
  conf.p["darknet_id"] = 0
  
  #assuming all models use same classes
  classes = utils.load_classes(conf.p["model_names"][0])
  
  yolo = []
  for model_id in range(len(conf.p["model_cfgs"])):
    yolo.append(cv.dnn.readNetFromDarknet(conf.p["model_cfgs"][model_id], conf.p["model_weights"][model_id]))
  
if __name__ == '__main__':
  main()
