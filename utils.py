'''*-----------------------------------------------------------------------*---
                                                         Author: Jason Ma
                                                         Date  : Sep 06 2018
                                 forward-vision

  File Name  : utils.py
  Description: Some useful things that CV module can utilize
---*-----------------------------------------------------------------------*'''

import os
import ast
import sys
import time
import datetime

import cv2 as cv
import numpy as np

class Config():
  def __init__(self):
    self.p = {}

  def parse_conf(self, fname):
    with open(fname, "r") as f:
      for line in f:
        line = line.strip()
        line = line.split("#")[0]
        line = line.split("=")

        if len(line) < 2:
          continue

        param = line[0].strip()
        value = line[1].strip()

        if param == "":
          continue

        value = ast.literal_eval(value)
        
        self.p[param] = value
    
    if "mode" not in self.p:
      print("[conf] No mode specified.")
      sys.exit(1)
    
    #configure additional params automatically depending on mode
    if self.p["mode"] == "live":
      self.p["using_dsm"] = 1
      self.p["using_camera"] = 1
    elif self.p["mode"] == "capture":
      self.p["using_dsm"] = 0
      self.p["using_camera"] = 1
    elif self.p["mode"] == "loop":
      self.p["using_dsm"] = 1
      self.p["using_camera"] = 0
    elif self.p["mode"] == "read":
      self.p["using_dsm"] = 0
      self.p["using_camera"] = 0
    elif self.p["mode"] == "dev":
      self.p["using_dsm"] = 1
      self.p["using_camera"] = 1

'''[gen_dir]-------------------------------------------------------------------
  Generates directory for new captures
----------------------------------------------------------------------------'''
def gen_dir(images_dir):
  print("[gen_dir] Checking for general directory at: " + images_dir)

  if not os.path.exists(images_dir):
    print("[gen_dir] Creating directory at: " + images_dir)
    os.makedirs(images_dir)
  
  subdir_count = 0
  while True:
    images_dir_subdir = os.path.join(images_dir, str(subdir_count))
    if not os.path.exists(images_dir_subdir):
      print("[gen_dir] Creating directory at: " + images_dir_subdir)
      os.makedirs(images_dir_subdir)
      images_dir_full = images_dir_subdir
      break
    else:
      subdir_count += 1
  
  with open('gen_dir.log', 'a') as f:
    f.write(images_dir_full + '\n')

  return images_dir_full

'''[load_image]----------------------------------------------------------------
  Loads image from given path and returns it
----------------------------------------------------------------------------'''
def load_image(filename, channel_type):
  print("[load] Loading:\t" + filename.split('/')[-1])
  return cv.imread(filename, channel_type)

'''[display_stacked]-----------------------------------------------------------
  Displays images stacked in specified grid pattern
----------------------------------------------------------------------------'''
def display_stacked(images, res, rows, cols):
  stacked_rows = []
  
  #pad the displayed image with empty space if not enough images to fill
  while len(images) < rows * cols:
    images.append(np.zeros((images[0].shape), np.uint8))
  
  for r in range(rows):
    for i in range(r * cols, r * cols + cols):
      images[i] = cv.resize(images[i], res, interpolation = cv.INTER_CUBIC)
      
      #convert all images to 3-channel images in RGB
      if len(images[i].shape) < 3:
        images[i] = cv.cvtColor(images[i], cv.COLOR_GRAY2RGB)
    
    #build up rows
    stacked_rows.append(np.concatenate(images[r * cols: r * cols + cols], axis=1))
  
  #build up full image with rows
  stacked_img = np.concatenate(stacked_rows, axis=0)

  cv.imshow("[stacked]", stacked_img)

"""[get_output_names]----------------------------------------------------------
  returns output layer class names
----------------------------------------------------------------------------"""
def get_output_names(net):
  layer_names = net.getLayerNames()
  return [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

"""[postprocess]---------------------------------------------------------------
  yolov3 postprocessing:
  - confidence filtering
  - non-max suppression
----------------------------------------------------------------------------"""
def postprocess(frame, outs, conf_threshold=0.25, nms_threshold=0.5):
  frame_h = frame.shape[0]
  frame_w = frame.shape[1]

  class_ids = []
  confs = []
  boxes = []
  
  #find all boxes that satisfy confidence threshold
  for out in outs:
    for detection in out:
      scores = detection[5:]
      class_id = np.argmax(scores)
      conf = scores[class_id]
      if conf > conf_threshold:
        x_center = int(detection[0] * frame_w)
        y_center = int(detection[1] * frame_h)
        w = int(detection[2] * frame_w)
        h = int(detection[3] * frame_h)
        left = int(x_center - w / 2)
        top = int(y_center - h / 2)

        class_ids.append(class_id)
        confs.append(float(conf))
        boxes.append([left, top, w, h])

  nms_boxes = []

  #print("[pp]", boxes)
  #print("[pp]", confs)
  
  #apply non-max suppression to qualifying boxes
  inds = cv.dnn.NMSBoxes(boxes, confs, conf_threshold, nms_threshold)
  for i in inds:
    i = i[0]
    box = boxes[i]
    class_id = class_ids[i]
    left = box[0]
    top = box[1]
    width = box[2]
    height = box[3]
    x_center = left + width / 2.0
    y_center = top + height / 2.0
    #print("[pp] c: %d xywh: %.3f %.3f %.3f %.3f" % (class_id, left, top, width, height))
    nms_boxes.append([box, class_id])
  return nms_boxes
