import os
import logging
import pdb

import cv2
import numpy as np

from utils import IMAGES_DIR

# from matplotlib import pyplot as plt


def do_nothing(x):
    pass


def update(frame):
    thresh1 = cv2.getTrackbarPos("thresh1", "frame")
    thresh2 = cv2.getTrackbarPos("thresh2", "frame")
    try:
        edges = cv2.Canny(frame, thresh1, thresh2)
    except cv2.error as e:
        edges = np.zeros(frame)
    cv2.imshow("frame", edges)


def main():
    pdb.set_trace()
    cv2.namedWindow("frame")
    frame_file = os.path.join(IMAGES_DIR, "calib_result.jpg")
    print(frame_file)
    frame = cv2.imread(frame_file)
    cv2.createTrackbar("thresh1", "frame", 0, 300, do_nothing)
    cv2.createTrackbar("thresh2", "frame", 0, 300, do_nothing)
    cv2.setTrackbarPos("thresh1", "frame", 200)
    cv2.setTrackbarPos("thresh2", "frame", 100)
    while frame is not None:
        update(frame)
        if cv2.waitKey(50) == ord("q"):
            break
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
