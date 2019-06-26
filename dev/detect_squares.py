"""
Detects polygons?
"""
import cv2
import numpy as np
from .colors import GREEN


def nothing(x):
    pass


# http://www.pyimagesearch.com/2014/08/04/opencv-python-color-detection/
cv2.namedWindow("detected circles", flags=cv2.WINDOW_NORMAL)


def polygon_recognition(frame, lower=127, upper=255, edge_ratio=0.01):
    image = frame.copy()
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _ret, thresh = cv2.threshold(gray_image, lower, upper, 1)
    _ret, contours, _h = cv2.findContours(thresh, 1, 2)
    for contour in contours:
        polygon = cv2.approxPolyDP(
            countour, edge_ratio * cv2.arcLength(contour, True), True
        )
        if len(polygon) < 4:
            cv2.drawContours(img, [contour], 0, GREEN, -1)


def main():
    filename = "buoytest2.jpg"
    edge_ratio = 0.01

    color_image = cv2.imread(filename)
    gray_image = cv2.imread(filename, 0)
    while True:
        img = color_image.copy()
        _ret, thresh = cv2.threshold(gray_image, 127, 255, 1)
        # thresh = cv2.Canny(img,100,200)
        _ret, contours, _h = cv2.findContours(thresh, 1, 2)
        for cnt in contours:

            poly = cv2.approxPolyDP(cnt, edge_ratio * cv2.arcLength(cnt, True), True)
            if len(poly) < 4:
                cv2.drawContours(img, [cnt], 0, (0, 255, 0), -1)
            elif len(poly) > 20:
                # Near circle
                cv2.drawContours(img, [cnt], 0, (0, 255, 255), -1)
            else:
                cv2.drawContours(img, [cnt], 0, (0, 0, 255), -1)
            cv2.imshow("detected circles", img)
            # cv2.waitKey(1)
            #
            # print len(poly)
            # if len(poly)==5:
            #     print "pentagon"
            #     cv2.drawContours(img,[cnt],0,255,-1)
            # elif len(poly)==3:
            #     print "triangle"
            #     cv2.drawContours(img,[cnt],0,(0,255,0),-1)
            # elif len(poly)==4:
            #     print "square"
            #     cv2.drawContours(img,[cnt],0,(0,0,255),-1)
            # elif len(poly) == 9:
            #     print "half-circle"
            #     cv2.drawContours(img,[cnt],0,(255,255,0),-1)
            # elif len(poly) > 15:
            #     print "circle"
            #     cv2.drawContours(img,[cnt],0,(0,255,255),-1)
        cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
