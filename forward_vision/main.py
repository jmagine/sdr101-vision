"""
forward_vision.py

main() is called by command line script
"""

import sys
import time
import argparse
import logging
import traceback
from ctypes import sizeof

import cv2
import numpy as np

import pydsm


from shared_buffers.constants import FORWARD_VISION_SERVER_ID, GATEPOLE, TARGET_LOCATION
from shared_buffers.vision import LocationArray
from shared_buffers.serialization import Pack, Unpack

from shared_buffers.master import Goals

from .camera import get_camera

log = logging.getLogger("forward_vision")

SERVER_ID = 45
CLIENT_ID = 0


def update_location_data(client):
    l = LocationArray()
    l.locations[0].x = 1
    l.locations[0].y = 1
    l.locations[0].z = 1
    l.locations[0].confidence = 1
    l.locations[0].loctype = GATEPOLE

    l.locations[1].x = 2
    l.locations[1].y = 2
    l.locations[1].z = 2
    l.locations[1].confidencwe = 2
    l.locations[1].loctype = GATEPOLE

    l.locations[2].x = 3
    l.locations[2].y = 3
    l.locations[2].z = 3
    l.locations[2].confidence = 3
    l.locations[2].loctype = GATEPOLE
    # Pack and send location data
    buf = Pack(l)
    client.setLocalBufferContents(TARGET_LOCATION, buf)


def run():
    with get_camera() as camera:
        time.sleep(0.1)
        log.debug("Initializing DSM Client")
        client = pydsm.Client(SERVER_ID, CLIENT_ID, True)
        log.debug("Initializing local buffer...")
        client.registerLocalBuffer(TARGET_LOCATION, sizeof(LocationArray), False)
        log.debug("Registering remote buffer..")
        client.registerRemoteBuffer(MASTER_GOALS, MASTER_SERVER_IP, MASTER_SERVER_ID)

        try:
            # Get goals buffer from master
            buf, active = client.getRemoteBufferContents(
                MASTER_GOALS, MASTER_SERVER_IP, MASTER_SERVER_ID
            )
            # Process goals buffer
            if buf and active:
                goals = Unpack(Goals, buf)
                goal = goals.forwardVision
                log.debug("Goal: %s", goal)
            else:
                goal = 0
                log.debug("No goal")
            # camera.capture(stream,'bgr')

            # cv2.imshow("Image", frame.array)
            cv2.waitKey(1)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            break
        finally:
            cv2.destroyAllWindows()


def main():
    """
    Entry point for forward_vision
    """
    try:
        run()
    except Exception as e:
        log.error(str(e))
        for line in traceback.format_exc():
            log.error(line)


if __name__ == "__main__":
    main()
