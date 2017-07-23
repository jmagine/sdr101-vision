"""
Wrapper for the picamera and OpenCV camera interfaces
The max resolution of the picamera is
2592x1944
with a bit depth of 10 and max framerate of 15

Camera sensor mode
# | Resolution  Aspect Ratio Framerates Video Image FoV Binning
--+-----------+------+-------------+---+---+---------+----------------
1 | 1920x1080 | 16:9 | 1-30fps     | x |   | Partial | None
2 | 2592x1944 | 4:3  | 1-15fps     | x | x | Full    | None
3 | 2592x1944 | 4:3  | 0.1666-1fps | x | x | Full    | None
4 | 1296x972  | 4:3  | 1-42fps     | x |   | Full    | 2x2
5 | 1296x730  | 16:9 | 1-49fps     | x |   | Full    | 2x2
6 | 640x480   | 4:3  | 42.1-60fps  | x |   | Full    | 4x4
7 | 640x480   | 4:3  | 60.1-90fps  | x |   | Full    | 4x4
"""
import sys
import os
import time
import logging
import datetime
import pdb
import argparse
import itertools

import numpy as np
import cv2

from .utils import ON_PI

log = logging.getLogger(__name__)

if ON_PI:
    import picamera
    import picamera.array

class Camera():
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        pass

    def setup(self):
        pass

class OpenCVCamera(Camera):
    def __init__(self, camera_id=0):
        self._camera = cv2.VideoCapture(camera_id)

    def close(self):
        self._camera.release()

    def next_frame(self):
        """Return a single frame"""
        succcess, frame = self._camera.read()
        if not succcess:
            raise IOError("Frame not read")
        return frame

    def setup(self):
        # self._camera.set()
        # self._camera.set()
        time.sleep(4)
        pass


class PiCamera(Camera):
    pass

class PiCameraLowFramerate(Camera):
    def __init__(self, resolution=(1024, 768), downsize=(320, 240)):
        self._camera = picamera.PiCamera()
        # self._camera.resolution = resolution
        self._stream = picamera.array.PiRGBArray(self._camera)
        self.downsize = downsize

        time.sleep(2)

    def next_frame(self):
        # capture(output, format=None, use_video_port=False, resize=None,
        #         splitter_port=0, **options)
        # self._camera.capture(self._stream, format='bgr', resize=self.downsize)
        self._stream.truncate()
        self._stream.seek(0)
        self._camera.capture(self._stream, format='bgr')
        # pdb.set_trace()
        return self._stream.array

    def frames(self):
        for i in itertools.count():
            yield from self._camera.capture_continuous()

    def close(self):
        self._camera.close()

    def setup(self):
        # self._camera.resolution = (2592, 1944)
        self._camera.meter_mode = 'backlit'
        self._camera.sensor_mode = 2
        # self._camera.framerate = 5
        time.sleep(2)
        self._camera.shutter_speed = self._camera.exposure_speed
        awb_gains = self._camera.awb_gains
        self._camera.awb_mode = 'off'
        self._camera.awb_gains = awb_gains
        self._camera.image_effect = 'none'
        self._camera.exposure_mode = 'off'
        # self._camera.denoise = True
        # self._camera.color_effects = None
        # self._camera.rotation = 0
        # self._camera.hflip = False
        # self._camera.vflip = False
        # self._camera.crop = (0.0, 0.0, 1.0, 1.0)
        # self._camera.sharpness = 0
        # self._camera.contrast = 0
        # self._camera.brightness = 50
        # self._camera.saturation = 0
        # self._camera.ISO = 0
        # self._camera.video_stabilization = False
        # self._camera.exposure_compensation = 0


def get_camera():
    if ON_PI:
        # return PiCameraLowFramerate(resolution=(1296, 972), downsize=(1296, 972))
        return PiCameraLowFramerate()
    else:
        return OpenCVCamera()

def main():
    """
    Image aqcuisition
    Entry point for take_pics
    """
    FORMAT = '%(asctime)s %(message)s'
    # DATE_FMT = '%()s'
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', action='store_true', help='Capture as numpy arrays')
    parser.add_argument('-o,', '--output', help='Output to file', default='images/')
    args = parser.parse_args()

    image_dir = os.path.normpath(args.output)
    if not os.path.isdir(image_dir):
        os.makedirs(image_dir)
    for i in itertools.count():
        run_dir = os.path.join(image_dir, 'run{:03d}'.format(i))
        if not os.path.isdir(run_dir):
            os.mkdir(run_dir)
            break

    logging.basicConfig(format=FORMAT, filename='log')
    log.addHandler(logging.StreamHandler(sys.stdout))

    try:
        camera = get_camera()
        camera.setup()
        for i in itertools.count():
            # now = datetime.datetime.now()
            frame = camera.next_frame()
            next_frame = 'image{:06d}.jpg'.format(i)
            frame_path = os.path.join(run_dir, next_frame)
            # np.savez_compressed(frame_file, frame)
            cv2.imwrite(frame_path, frame)
            print("Frame %s" % next_frame)
            log.info("Frame %s", next_frame)
    finally:
        camera.close()

if __name__ == '__main__':
    main()
