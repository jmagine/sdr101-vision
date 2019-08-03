'''*-----------------------------------------------------------------------*---
                                                         Author: Jason Ma
                                                         Date  : Aug 15 2018
                                     vision

  File: main.py
  Desc: Main application for vision module:
        - Continuously saves images to new directory for each capture
        - Can playback images from previous captures
        - Detects mission objectives using yolo
        - Prints or publishes detections to dsm
        Submodule config at config.cfg, including dsm, yolo, and cam.
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
  image_orange = None

  #[sanity checks]-------------------------------------------------------------
  if image is None:
    return 0, None, None
  
  height = image.shape[0]
  width = image.shape[1]
  channels = image.shape[2]

  #[preprocessing]-------------------------------------------------------------
  #resize images to low or mid res for faster processing
  if not conf.p["rgb"]:
    image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

  #send images through yolo and publish to DSM
  if conf.p["using_yolo"]:
    blob = cv.dnn.blobFromImage(image, 1/255.0, conf.p["res_model"][model_id], [0,0,0], 1, crop=False)
    yolo[model_id].setInput(blob)
    out = yolo[model_id].forward(utils.get_output_names(yolo[model_id]))
    boxes = utils.postprocess(image, out, conf_threshold=conf.p["yolo_conf_thres"], nms_threshold=conf.p["yolo_nms_thres"])
    boxes = utils.organize_dets(boxes)

    #if anything looks like path marker, find heading
    for box in boxes:
      heading = 0
      if classes[box[1][0]] == "marker":
        heading, image_orange = utils.find_heading(image, box[0])
        box[1][2] = heading

    #calc normalized coords
    for box in boxes:
      box[0][0] = float(box[0][0] / width)
      box[0][1] = float(box[0][1] / height)
      box[0][2] = float(box[0][2] / width)
      box[0][3] = float(box[0][3] / height)

    #publish or print detections while boxes are in normalized coords
    if conf.p["using_dsm"]:
      utils.pub_detections(client, conf.p["dsm_buffer_name"], conf.p["pred_id"], boxes, classes)
    else:
      utils.print_detections(conf.p["pred_id"], boxes, classes)

    #convert image and boxes res to res_display
    image_draw = cv.resize(image, conf.p["res_display"], interpolation = cv.INTER_CUBIC)
    for box in boxes:
      box[0][0] = int(box[0][0] * conf.p["res_display"][0])
      box[0][1] = int(box[0][1] * conf.p["res_display"][1])
      box[0][2] = int(box[0][2] * conf.p["res_display"][0])
      box[0][3] = int(box[0][3] * conf.p["res_display"][1])
     
    #use res_display coords for drawing
    image_pred = utils.draw_preds(image_draw, boxes, classes)
    
    t, _ = yolo[model_id].getPerfProfile()
    print("[yolo] t: %.2f model: %d %10s cam: %5d pred: %5d" % (t / cv.getTickFrequency(), model_id, conf.p["res_model"][model_id], image_id, conf.p["pred_id"]))
    
    #publish to dsm or print detections
    return len(boxes), image_pred, image_orange
  
'''[main]----------------------------------------------------------------------
  
----------------------------------------------------------------------------'''
def main():
  print("[init] Mode:\t%s" % (conf.p["mode"]))
  print("[init] dsm:\t%s" % (conf.p["using_dsm"]))
  print("[init] camera:\t%s" % (conf.p["using_camera"]))
  print("[init] disp:\t%s" % (conf.p["using_dsm"]))

  #init dsm client and buffers
  client = None
  if conf.p["using_dsm"]:
    print("[init] Initializing dsm")
    client = pydsm.Client(conf.p["dsm_server_id"], conf.p["dsm_client_id"], True)
    client.registerLocalBuffer(conf.p["dsm_buffer_name"], sizeof(DetectionArray), False)
    #time.sleep(1)
  
  #init camera
  c_t = None
  if conf.p["using_camera"]:
    print("[init] Initializing camera")
    c_t = capture_worker.cap_thread(conf.p["res_capture"], conf.p["output_dir"])
    c_t.start()
    os.makedirs(os.path.join(c_t.image_full_dir, conf.p["pred_dir"]))
  
  #init display
  d_t = None
  if conf.p["using_disp"]:
    print("[init] Initializing display")
    d_t = display_worker.display_thread(conf, c_t)
    d_t.start()

  #main loop
  model_id = 0
  try:
    while True:
      #use frames from stream
      if conf.p["using_camera"]:
        image = c_t.frame
        image_id = c_t.image_count

        if image is None:
          continue

      #read image from input dir
      else:
        #find all images
        #TODO clean this up a bit, looks stupid
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
      dets, image_pred, image_orange = process_image(image, client, model_id, image_id)
      
      if conf.p["using_camera"] and conf.p["using_yolo"]:
        cv.imwrite(os.path.join(c_t.image_full_dir, conf.p["pred_dir"], str(conf.p["pred_id"]) + ".jpg"), image_pred)

      if conf.p["using_yolo"]:
        conf.p["pred_id"] += 1

      #update predictions on display
      if conf.p["using_disp"]:
        if image_pred is not None:
          d_t.images[1] = image_pred
        if image_orange is not None:
          d_t.images[2] = image_orange
        
      #adaptive resolution
      if dets == 0:
        model_id = min(model_id + 1, len(conf.p["model_cfgs"]) - 1)
      else:
        model_id = max(model_id - 1, 0)
  except KeyboardInterrupt:
    print("[main] Ctrl + c received")
  #except Exception as e:
  #  print("[main] [error] %s" % (str(e)))

#TODO merge with main init
'''[init]----------------------------------------------------------------------
  Parses config, initializes vision modules
----------------------------------------------------------------------------'''
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

if conf.p["using_disp"]:
  import display_worker

if conf.p["using_yolo"]:
  conf.p["pred_id"] = 0
  
  #assuming all models use same classes
  classes = utils.load_classes(conf.p["model_names"][0])
  
  yolo = []
  for model_id in range(len(conf.p["model_cfgs"])):
    yolo.append(cv.dnn.readNetFromDarknet(conf.p["model_cfgs"][model_id], conf.p["model_weights"][model_id]))
  
if __name__ == '__main__':
  main()
