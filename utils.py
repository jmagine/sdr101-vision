'''*-----------------------------------------------------------------------*---
                                                         Author: Jason Ma
                                                         Date  : Sep 06 2018
                                     vision

  File: utils.py
  Desc: Some useful utilities for vision module, including a config parser,
        heading finder, custom detection handling, io
---*-----------------------------------------------------------------------*'''

import os
import ast
import sys
import time
import datetime

import cv2 as cv
import numpy as np

sys.path.append("/home/pi/DistributedSharedMemory/")
import pydsm

sys.path.append("/home/pi/python-shared-buffers/shared_buffers/")
from constants import *
from vision import Detection, DetectionArray
from serialization import *
from ctypes import sizeof
from master import *

'''[Config]--------------------------------------------------------------------
  Stores configuration for use in rest of vision
----------------------------------------------------------------------------'''
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
        
        print("[pc] loading: %-16s = %s" % (param, value))
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

'''[find_heading]--------------------------------------------------------------
  Find the angle of marker
----------------------------------------------------------------------------'''
def find_heading(image, box):
  
  heading = 0
  if image is None:
    return 0, None

  #assumes box is x,y,w,h
  x = box[0]
  y = box[1]
  w = box[2]
  h = box[3]

  H_HIGH = 30
  S_HIGH = 255
  V_HIGH = 255

  H_LOW = 0
  S_LOW = 0
  V_LOW = 20
  
  margin = 64

  sub_image = image[max(y - margin, 0) : min(int(y + margin + h / 2), image.shape[0]), max(x - margin, 0) : min(x + margin + w, image.shape[1])]
  image_hsv = cv.cvtColor(sub_image, cv.COLOR_BGR2HSV)
  #image_orange = sub_image
  image_orange = cv.inRange(image_hsv, (H_LOW, S_LOW, V_LOW), (H_HIGH, S_HIGH, V_HIGH))
  
  #resize so processing occurs faster
  image_orange = cv.resize(image_orange, (160, 128), interpolation = cv.INTER_CUBIC)
  height = image_orange.shape[0]
  width = image_orange.shape[1]
  
  top = [height + 1, -1]

  for y in range(height):
    total = 0
    count = 0
    found = False
    for x in range(width):
      if image_orange[y][x] == 255:
        total += x
        count += 1
        found = True
    if found:
      x_avg = float(total / count)
      heading = (x_avg - (width / 2)) / (width / 2)
      print("[find_heading] marker: %.2f" % (heading))
      break

  image_orange = cv.cvtColor(image_orange, cv.COLOR_GRAY2BGR)
  return heading, image_orange

'''[print_detections]----------------------------------------------------------
  Print deetections from YOLOv3
----------------------------------------------------------------------------'''
def print_detections(boxes, classes):
  for b in boxes:
    cls = b[1][0]
    cnf = b[1][1]
    cxt = b[1][2]
    idx = b[1][3]

    x = b[0][0] + b[0][2] / 2.0
    y = b[0][1] + b[0][3] / 2.0
    w = b[0][2]
    h = b[0][3]

    #context for sizes
    #forward classes
    if classes[cls] == "aswang":
      cxt = b[0][2] * b[0][3]
    elif classes[cls] == "draugr":
      cxt = b[0][2] * b[0][3]
    elif classes[cls] == "vetalas":
      cxt = b[0][2] * b[0][3]
    elif classes[cls] == "jiangshi":
      cxt = b[0][2] * b[0][3]

    #sanity check for cxt
    if cxt is None:
      cxt = 0

    print("[det] | %7s %.2f | %.4f | %.2f %.2f %.2f %.2f" % (classes[cls], cnf, cxt, x, y, w, h))

'''[pub_detections]------------------------------------------------------------
  Publishes detections from YOLOv3 to DSM
----------------------------------------------------------------------------'''
def pub_detections(client, buffer_name, boxes, classes):
  #init everything to 0
  d_a = DetectionArray()
  for i in range(8):
    d_a.detections[i].cls = 255
    d_a.detections[i].cnf = 0
    d_a.detections[i].x = 0
    d_a.detections[i].y = 0
    d_a.detections[i].w = 0
    d_a.detections[i].h = 0
    d_a.detections[i].cxt = 0
    d_a.detections[i].id = 0

  #if detections exist, fill them in
  for i, b in enumerate(boxes):
    d = Detection()
    d.cls = int(b[1][0])
    d.cnf = b[1][1]
    
    if b[1][2] is not None:
      d.cxt = b[1][2]
    d.id = b[1][3]

    d.x = b[0][0] + b[0][2] / 2.0
    d.y = b[0][1] + b[0][3] / 2.0
    d.w = b[0][2]
    d.h = b[0][3]
    
    #context for sizes
    #forward classes
    if classes[d.cls] == "aswang":
      d.cxt = b[0][2] * b[0][3]
    elif classes[d.cls] == "draugr":
      d.cxt = b[0][2] * b[0][3]
    elif classes[d.cls] == "vetalas":
      d.cxt = b[0][2] * b[0][3]
    elif classes[d.cls] == "jiangshi":
      d.cxt = b[0][2] * b[0][3]

    #sanity check for cxt
    if d.cxt is None:
      d.cxt = 0

    d_a.detections[i] = d

    print("[pub] | %7s %.2f | %.4f | %.2f %.2f %.2f %.2f" % (classes[d.cls], d.cnf, d.cxt, d.x, d.y, d.w, d.h))
  
  client.setLocalBufferContents(buffer_name, pack(d_a))

'''[draw_preds]----------------------------------------------------------------
  Draws YOLO predictions onto image with class and conf  
----------------------------------------------------------------------------'''
def draw_preds(image, boxes, classes):
  image_preds = image.copy()
  
  for b in boxes:
    cls = b[1][0]
    cnf = b[1][1]
    cxt = b[1][2]
    x = b[0][0]
    y = b[0][1]
    w = b[0][2]
    h = b[0][3]

    #bounding box around detection
    cv.rectangle(image_preds, (x, y), (x + w, y + h), (0, 255, 0), 1)
    
    #text label on detection
    label = "%s %.2f" % (classes[cls], cnf)
    label_size, base_line = cv.getTextSize(label, cv.FONT_HERSHEY_PLAIN, 0.5, 1)
    y = max(y, label_size[1])
    x = min(x, image.shape[1] - label_size[0])
    cv.rectangle(image_preds, (x, y - label_size[1]), (x + label_size[0], y + base_line), (255, 255, 255), cv.FILLED)
    cv.putText(image_preds, label, (x, y), cv.FONT_HERSHEY_PLAIN, 0.5, (0, 0, 0), 1, cv.LINE_AA)
  return image_preds

'''[get_output_names]----------------------------------------------------------
  returns output layer class names
----------------------------------------------------------------------------'''
def get_output_names(net):
  layer_names = net.getLayerNames()
  return [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

'''[organize_dets]-------------------------------------------------------------
  Sort detections by x coord
----------------------------------------------------------------------------'''
def organize_dets(boxes):
  for i1 in range(len(boxes)):
    for i2 in range(len(boxes)):
      if boxes[i1][0][0] < boxes[i2][0][0]:
        temp = boxes[i2].copy()
        boxes[i2] = boxes[i1]
        boxes[i1] = temp

  return boxes

'''[postprocess]---------------------------------------------------------------
  yolov3 postprocessing:
  - confidence filtering
  - non-max suppression
----------------------------------------------------------------------------'''
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

  #apply non-max suppression to qualifying boxes
  inds = cv.dnn.NMSBoxes(boxes, confs, conf_threshold, nms_threshold)
  for i in inds:
    i = i[0]
    box = boxes[i]
    class_id = class_ids[i]
    conf = confs[i]
    left = box[0]
    top = box[1]
    width = box[2]
    height = box[3]
    x_center = left + width / 2.0
    y_center = top + height / 2.0
    #print("[pp] c: %d xywh: %.3f %.3f %.3f %.3f" % (class_id, left, top, width, height))
    nms_boxes.append([box, [class_id, conf, None, None]])
  return nms_boxes

'''[load_classes]--------------------------------------------------------------
  Load classes from names file
----------------------------------------------------------------------------'''
def load_classes(class_file):
  classes = None
  with open(class_file, 'rt') as f:
    classes = f.read().rstrip("\n").split("\n")
  return classes

'''[stack_images]--------------------------------------------------------------
  Stacks images in specified grid pattern
----------------------------------------------------------------------------'''
def stack_images(images, res, rows, cols):
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

  return stacked_img

'''[gen_dir]-------------------------------------------------------------------
  Generates directory for new captures
----------------------------------------------------------------------------'''
def gen_dir(images_dir):
  print("[gen_dir] Checking dir: " + images_dir)

  if not os.path.exists(images_dir):
    print("[gen_dir] Creating dir: " + images_dir)
    os.makedirs(images_dir)
  
  subdir_count = 0
  while True:
    images_dir_subdir = os.path.join(images_dir, str(subdir_count))
    if not os.path.exists(images_dir_subdir):
      print("[gen_dir] Creating dir: " + images_dir_subdir)
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

