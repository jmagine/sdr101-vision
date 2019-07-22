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

import cv2
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
    utils.display_stacked(images, RES_240, 1, 1)
  
    #do not wait for input, but wait enough to display images
    # also holding q will usually allow the pi to quit
    if conf.p["display_type"] == "no_input":
      key = cv2.waitKey(50)
      if key == ord('q'):
        print("[proc] Detected q, exiting")
        sys.exit(0)

    #wait for input from user, use space or arrow keys to advance/nav stream
    elif conf.p["display_type"] == "wasd_input":
      print("[proc] wasd")
      key = ''
      while True:
        key = cv2.waitKey(1000)
        if key == ord('q'):
          print("[proc] Detected q, exiting")
          sys.exit(0)

        #left
        elif key == ord('a'):
          conf.p["read_pos"] -= 100
          break
        #right
        elif key == ord('d') or key == ord(' '):
          conf.p["read_pos"] += 100
          break

  return 0, 0, 0


"""[dev_process_image]---------------------------------------------------------
  DEBUG template processing func for image dir
----------------------------------------------------------------------------"""
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

"""[detect]--------------------------------------------------------------------
  Returns a list of detections from darknet-nnpack-custom output string
----------------------------------------------------------------------------"""
def detect(s):
  detections = []

  if len(s) < 2:
    return detections

  for i in range(2, len(s)):
    box = re.findall("\d+\.\d+", s[i])
    box = [float(x) for x in box]
    
    if len(box) < 5:
      continue
    
    d = Detection()
    d.x = box[1] + box[3] / 2.0
    d.y = box[2] + box[4] / 2.0
    d.w = box[3]
    d.h = box[4]

    #TODO currently size is just height, set to width * height or remove in future
    d.size = box[4]

    cls = s[i].split(":")[0]
    if "aswang" in cls:     d.cls = 0
    elif "draugr" in cls:   d.cls = 1
    elif "vetalas" in cls:  d.cls = 2
    elif "jiangshi" in cls: d.cls = 3
    elif "gate" in cls:     d.cls = 4
    elif "bat" in cls:      d.cls = 5
    elif "wolf" in cls:     d.cls = 6
    #d.cls = s[i].split(":")[0].encode("UTF-8")
    detections.append(d)

  for d in detections:
    print("[pub] c: %3d\tx: %.3f\ty: %.3f\tw: %.3f\th: %.3f" % (d.cls, d.x, d.y, d.w, d.h))

  return detections

"""[pub_detections]------------------------------------------------------------
  Publishes detections to DSM
----------------------------------------------------------------------------"""
def pub_detections(client, detections):
  #print("[pub] start")
  d_a = DetectionArray()
  for i in range(8):
    d_a.detections[i].cls = 255
    d_a.detections[i].x = 0
    d_a.detections[i].y = 0
    d_a.detections[i].w = 0
    d_a.detections[i].h = 0
    d_a.detections[i].size = 0

  for i, d in enumerate(detections):
    d_a.detections[i] = d
  
  client.setLocalBufferContents("forwarddetection", pack(d_a))

"""[subprocess_wait]-----------------------------------------------------------
  Hangs until darknet-nnpack-custom waits for input
----------------------------------------------------------------------------"""
def subprocess_wait():
  #print("[sp_wait] start")
  out = ""
  ready = False
  while not ready:
    yolo_proc.stdout.flush()
    stdout_line = yolo_proc.stdout.readline()

    if not stdout_line:
      continue

    stdout_line = stdout_line.decode("UTF-8")
    out += stdout_line
    if "Enter Image Path" in out:
      ready = True
  
  print("[sp_wait] %s" % out)
  return out

"""[yolo]----------------------------------------------------------------------
  Feeds an image using path into yolov3-tiny for detection.
----------------------------------------------------------------------------"""
def yolo(image_dir, image_name):
  global darknet_frame
  try:
    image_path = os.path.join(image_dir, image_name)
    image_num = 0
    image_num = int(image_name.split(".")[0])

    print("[yolo] [feed] %s" % (image_path))
    try:
      prediction = cv2.imread(os.path.join(darknet_base_dir, "predictions.png"))
      copyfile(os.path.join(darknet_base_dir, "predictions.png"), 
               os.path.join(image_dir, "darknet", "pred_%d_%d.jpg" % (image_num, darknet_frame)))
      darknet_frame += 1
    except Exception as e:
      print("[yolo] exception inner: %s" % str(e))
      pass
    
    image_path = image_path + "\n"
    yolo_proc.stdin.write(image_path.encode())
    yolo_proc.stdin.flush()
    #time.sleep(2)
    out = subprocess_wait()
    
  except Exception as e:
    print("[yolo] exception outer: %s" % str(e))
    pass
  #print("[yolo] complete", yolo_proc.poll())
  return out.split("\n")

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
    client.registerLocalBuffer("forwarddetection", sizeof(DetectionArray), False)
    
    print("[init] DSM init complete")
  #handle directory creation for saving images
  # - output_dir should already exist, but create one if not there
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

  #TODO move this to a sep func if possible, def process(mode, c_t=None)
  
  #use process func
  if conf.p["mode"] == "live":
    try:
      while True:
        #generate list of all image names
        image_list = os.listdir(c_t.image_full_dir)
        image_list.remove("darknet")
        image_list.sort(key = lambda x: int(x.split(".")[0]), reverse=True)
        
        if len(image_list) < 3:
          print("[live] Stream not initialized yet")
          time.sleep(1)
          continue
        
        #do not use the first image because stream could still be writing to it
        last_image_file = image_list[2]
        
        #load a recent image in
        image = utils.load_image(os.path.join(c_t.image_full_dir, last_image_file), COLOR_RGB)
        process_image(image)
        
        if conf.p["using_darknet_nnpack"]:
          out = yolo(c_t.image_full_dir, last_image_file)
          detections = detect(out)
          if conf.p["using_dsm"]:
            pub_detections(client, detections)
        else:
          time.sleep(1)
    
    except KeyboardInterrupt:
      print("[main] Ctrl + c detected, breaking")
      print("[main] Full output path: %s" % (c_t.image_full_dir))

  #custom processing func with dsm
  if conf.p["mode"] == "dev":
    read_pos = conf.p["read_pos"]
    #generate list of all image names
    image_list = os.listdir(conf.p["input_dir"])
    image_list.sort(key = lambda x: int(x.split(".")[0]))
    
    #such turing machine
    while read_pos >= 0 and read_pos < len(image_list):
      if image_list[read_pos].split(".")[1] != "jpg":
        del image_list[read_pos]

      image = utils.load_image(os.path.join(conf.p["input_dir"], str(image_list[read_pos])), COLOR_RGB)
      process_image(image)
      read_pos = conf.p["read_pos"]

      if conf.p["using_darknet_nnpack"]:
        out = yolo(conf.p["input_dir"], str(image_list[read_pos]))
        detections = detect(out)
        if conf.p["using_dsm"]:
          pub_detections(client, detections)

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

  #just capture images, no processing
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
      #utils.pub_detections(client, 0, x, y, confidence, image_count % 256)
  
  #processes files in input_dir without publishing to dsm
  elif conf.p["mode"] == "read":

    read_pos = conf.p["read_pos"]
    #generate list of all image names
    image_list = os.listdir(conf.p["input_dir"])
    image_list.remove("darknet")
    image_list.sort(key = lambda x: int(x.split(".")[0]))
    #such turing machine
    while read_pos >= 0 and read_pos < len(image_list):
      if image_list[read_pos].split(".")[1] != "jpg":
        del image_list[read_pos]


      read_pos = conf.p["read_pos"]

      if conf.p["using_darknet_nnpack"]:
        out = yolo(conf.p["input_dir"], str(image_list[read_pos]))
        detections = detect(out)
      
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
  import pydsm

if conf.p["using_camera"]:
  from picamera.array import PiRGBArray
  from picamera import PiCamera

if conf.p["using_darknet_nnpack"]:
  from subprocess import run, Popen, PIPE, STDOUT
  import fcntl
  from shutil import copyfile
  darknet_base_dir = conf.p["darknet_nnpack_dir"]
  yolo_proc = Popen([os.path.join("./darknet"),
                     "detector",
                     "test",
                     os.path.join("cfg", "robosub.data"),
                     os.path.join("cfg", "yolov3-tiny-obj.cfg"),
                     os.path.join("yolov3-tiny-obj_final.weights"),
                     ],#os.path.join(conf.p["input_dir"], "0.jpg")],#"-thresh","0.1"],
                     stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=darknet_base_dir)
  fcntl.fcntl(yolo_proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
  #output = yolo_proc.stdout.read()
  #print(output)
  darknet_frame = 0

  subprocess_wait()
  #os.makedirs(os.path.join(conf.p["output_dir"], "darknet"))
  
if __name__ == '__main__':
  main()