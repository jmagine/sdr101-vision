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
import sys
import time

import cv2
import numpy as np

'''[Global vars]------------------------------------------------------------'''

config_file = "config.cfg"
#color codes for opencv
COLOR_RGB  = 1
COLOR_GRAY = 0
COLOR_ASIS = -1

#image shapes (width, height) for use with opencv
RES_1944 = (2592, 1944)
RES_1080 = (1920, 1080)
RES_720 = (960, 720)
RES_480 = (640, 480)
RES_240 = (320, 240)

#location to save images in live mode
#IMAGES_DIR = "/home/pi/ForwardVision/images/buoy_test/"
#READ_POS = 662

PRINT_TIMING = True

'''[process_image]-------------------------------------------------------------
  Function to handle processing of image

  image - input image array
  
  max_x - most confident x coordinate
  max_y - most confident y coordinate
  confidence - confidence in range [0,255] for detection
----------------------------------------------------------------------------'''
def process_image(image):
  
  #global READ_POS
  
  #[sanity checks]-------------------------------------------------------------
  if image is None:
    print("[proc] Image is None")
    sys.exit(1)
  
  #[preprocessing]-------------------------------------------------------------
  start = time.time()
  
  #resize images to low or mid res for faster processing
  #image = cv2.resize(image, conf.p["res_process"], interpolation = cv2.INTER_CUBIC)
  
  end = time.time()

  if PRINT_TIMING:
    print("[proc] Preproc:\t%.5f" % (end - start))

  #send images through darknet and publish to DSM

  #display images
  if conf.p["display_type"] != "no_disp":
    images = []
    images.append(image)
    utils.display_stacked(images, RES_240, 3, 3)
  
    #do not wait for input, but wait enough to display images
    # also holding q will usually allow the pi to quit
    if conf.p["display_type"] == "no_input":
      key = cv2.waitKey(50)
      if key == ord('q'):
        print("[proc] Detected q, exiting")
        sys.exit(0)

    #wait for input from user, use space or arrow keys to advance/nav stream
    elif conf.p["display_type"] == "wasd_input":
      key = ''
      while True:
        key = cv2.waitKey(100000)
        if key == ord('q'):
          print("[proc] Detected q, exiting")
          sys.exit(0)

        #left
        #elif key == ord('a'):
        #  READ_POS -= 1
        #  break
        #right
        #elif key == ord('d') or key == ord(' '):
        #  READ_POS += 1
        #  break

  #return max_x, max_y, int(max_count * 255 / total_count)
  return 0, 0, 0

def dev_process_image(image_dir):
  
  #generate list of all image names
  image_list = os.listdir(image_dir)
  image_list.sort(key = lambda x: int(x.split(".")[0]), reverse=True)
  
  if len(image_list) < 2:
    print("[dev] Stream not initialized yet")
    return
  
  #do not use the first image because stream could still be writing to it
  last_image_file = image_list[1]

  #load a recent image in
  image = utils.load_image(os.path.join(image_dir, last_image_file), COLOR_RGB)
  
  #process image

  #display image

'''[main]----------------------------------------------------------------------
  Main driver, creates file structure for images, handles existing/non-existing
  directories, and feeds images into process_image() for target detection.

  In live mode, this reads images from a Pi camera, writes them to a file, 
  processes the images, and publishes results to DSM buffer. It is also capable
  of displaying images, but will not wait for user input. Images are taken in
  either after an interval or as soon as the processing is done, whichever is
  later.

  In read mode, this feeds images in from a directory, processes the images,
  and displays the results while waiting for user input to continue or quit
----------------------------------------------------------------------------'''
def main():
  print("[init] Mode: %s" % (conf.p["mode"]))
  #only init dsm client and buffers if necessary
  if conf.p["using_dsm"]:
    print("[init] Initializing DSM client")
    client = pydsm.Client(conf.p["dsm_server_id"], conf.p["dsm_client_id"], True)

    print("[init] Initializing local buffers")
    client.registerLocalBuffer(TARGET_LOCATION, sizeof(Location), False)
    
    print("[init] DSM init complete")
  #handle directory creation for saving images
  # - output_dir should already exist, but create one if not there
  if conf.p["using_camera"]:
    print("[init] Camera init start")
    import capture_worker
    try:
      c_t = capture_worker.cap_thread(conf.p["res_capture"], conf.p["output_dir"])
      c_t.start()
    except Exception as e:
      print("[main] [error]: " + str(e))
    print("[init] Camera init complete")

  #TODO move this to a sep func if possible, def process(mode, c_t=None)
  
  #use process func
  if conf.p["mode"] == "live":
    try:
      while True:
        #generate list of all image names
        image_list = os.listdir(c_t.image_full_dir)
        image_list.sort(key = lambda x: int(x.split(".")[0]), reverse=True)
        
        if len(image_list) < 2:
          print("[live] Stream not initialized yet")
          time.sleep(1)
          continue
        
        #do not use the first image because stream could still be writing to it
        last_image_file = image_list[1]

        #load a recent image in
        image = utils.load_image(os.path.join(c_t.image_full_dir, last_image_file), COLOR_RGB)
        process_image(image)
        time.sleep(1)
    except KeyboardInterrupt:
      print("[main] Ctrl + c detected, breaking")
      print("[main] Full output path: %s" % (c_t.image_full_dir))

  #use dev process func
  if conf.p["mode"] == "dev":
    try:
      while True:
        dev_process_image(c_t.image_full_dir)
        time.sleep(1)
    except KeyboardInterrupt:
      print("[main] Ctrl + c detected, breaking")
      print("[main] Full output path: %s" % (c_t.image_full_dir))

  #no processing
  if conf.p["mode"] == "capture":
    try:
      while True:
        time.sleep(1)
    except KeyboardInterrupt:
      print("[main] Ctrl + c detected, breaking")
      print("[main] Full output path: %s" % (c_t.image_full_dir))
  
  #TODO clean this up, currently not working
  if conf.p["mode"] == "loop":
    IMAGES_SUBDIR = "comp/buoys_1"

    image_count = 0
    for i in range(1584, 1687):
      image = utils.load_image(os.path.join(conf.p["input_dir"], str(i) + ".jpg"), COLOR_RGB)
      x, y, confidence = process_image(image)
      image_count += 1
      #pack and publish results to DSM buffer
      utils.pub_loc(client, 0, x, y, confidence, image_count % 256)
  
  #TODO untested
  elif conf.p["mode"] == "read":

    read_pos = conf.p["read_pos"]
    #generate list of all image names
    image_list = os.listdir(conf.p["input_dir"])
    image_list.sort(key = lambda x: int(x.split(".")[0]))
    
    #such turing machine
    while read_pos >= 0 and read_pos < len(image_list):
      image = utils.load_image(os.path.join(conf.p["input_dir"], str(image_list[read_pos])), COLOR_RGB)
      process_image(image)

      if read_pos < 0 or read_pos >= len(image_list):
        print("[main] Exit? y/n")

        while True:
          key = cv2.waitKey(100000)

          if key == ord('q') or key == ord('y'):
            sys.exit(0)
          elif key == ord('n'):
            if read_pos < 0:
              read_pos = len(image_list) - 1
            else:
              read_pos = 0
            break

  

conf = utils.Config()
conf.parse_conf("config.cfg")

#conditional imports which require integration with rest of system
if conf.p["using_dsm"]:
  sys.path.append("/home/pi/DistributedSharedMemory/")
  sys.path.append("/home/pi/PythonSharedBuffers/src/")

  import pydsm
  from Constants import *
  from Vision import Location
  from Serialization import *
  from ctypes import sizeof
  from Master import *

if conf.p["using_camera"]:
  from picamera.array import PiRGBArray
  from picamera import PiCamera

if __name__ == '__main__':
  main()


