"""
Handles DSM server running etc
"""
import sys
import argparse
import ipaddress
import subprocess
import threading

from utils import ON_PI

import pydsm

from shared_buffers.constants import (
    FORWARD_VISION_SERVER_IP,
    FORWARD_VISION_SERVER_ID,
    GOAL_NONE,
    GOAL_FIND_GATE,
    GOAL_FIND_PATH,
    GOAL_FIND_RED_BUOY,
    GOAL_FIND_YELLOW_BUOY,
    GOAL_FIND_GREEN_BUOY,
    GOAL_FIND_PATH,
    GOAL_FIND_OCTAGON,
)

GOALS = []


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


def validate_ip(addr):
    try:
        ipaddress.ip_address(addr)
    except ValueError:
        return False
    return True


def start_server():
    subprocess.Popen(cmd, shell=True)


def main():
    """
    Dummy DSM testing
    """
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


if __name__ == "__main__":
    main()
