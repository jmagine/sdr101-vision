#!/usr/bin/python3
import sys
sys.path.append("../include/")
sys.path.append("../../PythonSharedBuffers/src/")
import cv2 as cv
import numpy as np
import pydsm as dsm
import time
from Constants import *
from Vision import ForwardVision
from Serialization import *

from picamera.array import PiRGBArray
from picamera import PiCamera
 
camera = PiCamera()
rawCapture = PiRGBArray(camera)
'''                                                                               # camera config
camera.sharpness = 0
camera.contrast = 0
camera.brightness = 50
camera.saturation = 0
camera.ISO = 0
camera.video_stabilization = False
camera.exposure_compensation = 0
camera.exposure_mode = 'auto'
camera.meter_mode = 'average'
camera.awb_mode = 'auto'
camera.image_effect = 'none'
camera.color_effects = None
camera.rotation = 0
camera.hflip = False
camera.vflip = False
camera.crop = (0.0, 0.0, 1.0, 1.0)
'''
if __name__ == "__main__":                                                     # main
    serverID = 45
    clientID = 0
    print("Initializing DSM Client")
    client = dsm.Client(serverID, clientID, True)
    print("""Finished initializing DSM Client\n
    Initializing local buffer:""")
    client.registerLocalBuffer(TARGET_LOCATION, 78, False)
    print("Finished initializing local buffer.")
    while True:                                                                # process every frame
        #camera.capture(rawCapture, format="bgr")
        #rawCapture.seek(0)
        #rawCapture.truncate()
            
        #print("frame %dx%d"%(len(rawCapture.array),len(rawCapture.array[0])))
        #cv.imshow("Image", rawCapture.array)
        l = ForwardVision()
        l.locations[0].x = 10.5
        l.locations[0].y = 0
        l.locations[0].z = 255.999
        l.locations[0].conf = 255
        l.locations[0].obj = GATEPOLE
        l.locations[1].x = 10.5
        l.locations[1].y = 0
        l.locations[1].z = 255.999
        l.locations[1].conf = 255
        l.locations[1].obj = GATEPOLE
        buf = Pack(l)
        print(list(buf))
        client.setLocalBufferContents(TARGET_LOCATION,buf)
        buf = client.getLocalBufferContents(TARGET_LOCATION)
        print(Unpack(ForwardVision,buf))
        time.sleep(2)
    cv.destroyAllWindows()
