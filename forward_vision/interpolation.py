"""
Gets the average
"""
import numpy as np
import cv2

def hsv_interpolate(hsv1, hsv2, ratio=0.5):

def rgb_interpolate(rgb1, rgb2, ratio=0.5):
    return np.array(rgb1 * ratio + rgb2 * (1 - ratio), dtype=np.uint8)

def main():
    for i in range(1, 67):
        frame = cv2.imread('blur/frame{:03d}.bmp'.format(i))
        # gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # hue_avg = np.average(hsv[:, :, 0])
        b_avg = np.average(frame[:, :, 0])
        g_avg = np.average(frame[:, :, 1])
        r_avg = np.average(frame[:, :, 2])
        h_avg = cv2.cvtColor(np.uint8([[[b_avg, g_avg, r_avg]]]),
                             cv2.COLOR_BGR2HSV)[0][0][0]
        sat_avg = np.average(hsv[:, :, 1])
        print("Average sat: {}".format(sat_avg))
        print("Average hue: {}".format(h_avg))
        lower_blue = np.array([h_avg - 2, sat_avg - 50, 127])
        upper_blue = np.array([h_avg + 2, sat_avg + 30, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        mask = cv2.bitwise_not(mask)
        res = cv2.bitwise_and(frame, frame, mask=mask)

        # maxr = 0
        # _,contours,h = cv2.findContours(mask,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
        # for cnt in contours:
        #     maxr = 0
        #     area = cv2.contourArea(cnt)

        #     apx = cv2.approxPolyDP(cnt,0.04*cv2.arcLength(cnt,True),True)

        #     #ratio = area / (np.pi*(radius**2))

        #     if (len(apx)<3):
        #         cv2.drawContours(res,[cnt],0,(0,255,0),-1)
        #     elif (len(apx)>4):
        #         cv2.drawContours(res,[cnt],0,(0,0,255),-1)
        #         if cv2.isContourConvex(apx):
        #             (x,y),radius = cv2.minEnclosingCircle(apx)
        #             center = (int(x),int(y))
        #             radius = int(radius)
        #             cv2.circle(res,center,radius,(127,0,255),3)
        #     else:
        #         cv2.drawContours(res,[cnt],0,(0,255,255),-1)
        # blur = cv2.bilateralFilter(frame,9,75,75)
        # res = blur
        cv2.imwrite('frame_out2/frame{:03d}.bmp'.format(i), res)
        print('frame {:u}'.format(i))
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
