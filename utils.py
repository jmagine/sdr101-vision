'''*-----------------------------------------------------------------------*---
                                                         Author: Jason Ma
                                                         Date  : Sep 06 2018
                                 forward-vision

  File Name  : utils.py
  Description: Some useful things that CV module can utilize
---*-----------------------------------------------------------------------*'''

import os
import sys
import time
import datetime

import cv2
import numpy as np

'''[gen_timestamp_dir]---------------------------------------------------------
  Generates timestamp for directory based on current date and time
----------------------------------------------------------------------------'''
def gen_timestamp_dir(images_dir):
  now = datetime.datetime.now()
  print("[gen tsd] Current time is: " + str(now))

  now = str(now).split(".")[0]
  now = now.replace(" ", "/")
  now = now.replace(":", "_")
  
  print("[gen tsd] Checking for general directory at: " + images_dir)
    
  #DEBUG set now to hardcode image subdir
  #now = "TEST"

  if not os.path.exists(images_dir):
    print("[gen tsd] Creating directory at: " + images_dir)
    os.makedirs(images_dir)

  images_dir_subdir = images_dir + now
  if not os.path.exists(images_dir_subdir):
    print("[gen tsd] Creating directory at: " + images_dir_subdir)
    os.makedirs(images_dir_subdir)
    images_dir_full = images_dir_subdir + "/"
  else:
    print("[gen tsd] Directory already exists. Creating at next available")
    i = 0
    images_dir_subdir_tail = images_dir_subdir + "-" + str(i) + "/"
    while True:
      if not os.path.exists(images_dir_subdir_tail):
        print("[gen tsd] Found spot. Creating directory at: " + images_dir_subdir_tail)
        os.makedirs(images_dir_subdir_tail)
        images_dir_full = images_dir_subdir_tail
        break
      i += 1
      images_dir_subdir_tail = images_dir_subdir + "-" + str(i) + "/"
  
  with open('gen_timestamp_dir.log', 'a') as f:
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
  print()
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
