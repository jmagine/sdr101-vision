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

import cv2
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
      self.p["display_type"] = "no_disp"
    elif self.p["mode"] == "capture":
      self.p["using_dsm"] = 0
      self.p["using_camera"] = 1
      self.p["display_type"] = "no_input"
    elif self.p["mode"] == "loop":
      self.p["using_dsm"] = 1
      self.p["using_camera"] = 0
      self.p["display_type"] = "no_input"
    elif self.p["mode"] == "read":
      self.p["using_dsm"] = 0
      self.p["using_camera"] = 0
      self.p["display_type"] = "wasd_input"
    elif self.p["mode"] == "dev":
      self.p["using_dsm"] = 1
      self.p["using_camera"] = 1
      self.p["display_type"] = "no_input"

'''[gen_dir]---------------------------------------------------------
  Generates directory for new captures
----------------------------------------------------------------------------'''
def gen_dir(images_dir):
  print("[gen tsd] Checking for general directory at: " + images_dir)

  if not os.path.exists(images_dir):
    print("[gen tsd] Creating directory at: " + images_dir)
    os.makedirs(images_dir)
  
  subdir_count = 0
  while True:
    images_dir_subdir = os.path.join(images_dir, str(subdir_count))
    if not os.path.exists(images_dir_subdir):
      print("[gen tsd] Creating directory at: " + images_dir_subdir)
      os.makedirs(images_dir_subdir)
      images_dir_full = images_dir_subdir
      break
    else:
      subdir_count += 1
  
  with open('gen_dir.log', 'a') as f:
    f.write(images_dir_full + '\n')

  return images_dir_full

'''[pub_loc]-------------------------------------------------------------------
  Publishes location to DSM buffer
----------------------------------------------------------------------------'''
def pub_loc(client, x, y, z, conf, loctype):
  l = Location()
  l.x = x
  l.y = y
  l.z = z
  l.confidence = conf
  l.loctype = loctype
  client.setLocalBufferContents(TARGET_LOCATION, Pack(l))
  print("[main] [dsm] publishing x:" + str(l.x) + " y:" + str(l.y) + " z:" + str(l.z) + " id:" + str(l.loctype) + " c:" + str(l.confidence))
  
'''[load_image]----------------------------------------------------------------
  Loads image from given path and returns it
----------------------------------------------------------------------------'''
def load_image(filename, channel_type):
  print("[load] Loading:\t" + filename.split('/')[-1])
  return cv2.imread(filename, channel_type)

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
      images[i] = cv2.resize(images[i], res, interpolation = cv2.INTER_CUBIC)
      
      #convert all images to 3-channel images in RGB
      if len(images[i].shape) < 3:
        images[i] = cv2.cvtColor(images[i], cv2.COLOR_GRAY2RGB)
    
    #build up rows
    stacked_rows.append(np.concatenate(images[r * cols: r * cols + cols], axis=1))
  
  #build up full image with rows
  stacked_img = np.concatenate(stacked_rows, axis=0)

  cv2.imshow("All imgs", stacked_img)

