"""
Runs a color threshold processing
"""
import cv2
import numpy as np

from .camera import get_camera

# HSV Thresholds
LOWER_BLUE = np.array([110, 50, 50])
UPPER_BLUE = np.array([130, 255, 255])

def main():
    with get_camera() as camera:
        while True:
            # Take each frame
            frame = camera.next_frame()

            # Convert BGR to HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Threshold the HSV image to get only blue colors
            mask = cv2.inRange(hsv, LOWER_BLUE, UPPER_BLUE)

            # Bitwise-AND mask and original image
            res = cv2.bitwise_and(frame,frame, mask= mask)

            cv2.imshow('frame',frame)
            cv2.imshow('mask',mask)
            cv2.imshow('res',res)
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break


if __name__ == '__main__':
    main()
