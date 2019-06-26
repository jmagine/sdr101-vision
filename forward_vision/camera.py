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

FORMAT = "%(asctime)s[%(name)24s|%(levelname)5s] %(message)s"
STREAM_FORMAT = "[%(asctime)s][%(levelname)5s] %(message)s"
DATE_FMT = "%m-%d-%Y %H:%M:%S"
STREAM_DATE_FMT = "%H:%M:%S"

if ON_PI:
    import picamera
    import picamera.array
    from picamera.encoders import PiCameraResolutionRounded


class Camera:
    """
    Wrapper class for picamera to allow for different inputs
    """

    def __init__(self):
        raise NotImplementedError()

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        """
        Close the camera
        """
        raise NotImplementedError()

    def setup(self):
        """
        Setup for the camera
        """
        raise NotImplementedError

    def next_frame(self):
        """
        Grab the next frame
        """
        raise NotImplementedError()


class DummyFrameCamera(Camera):
    """
    Returns frames as if they were camera frames.
    For testing.
    """


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
        time.sleep(1)
        # take a few pics to calibrate brightness / AWB ?


class PiCamera(Camera):
    """picamera that takes full resolution images at a slow (~2 fps)
    framerate
    """

    def __init__(self, auto_awb=True, awb_gains=(1.1, 1.9), resolution=(720, 480)):
        self._camera = picamera.PiCamera()
        # self._camera.resolution = resolution
        self._stream = picamera.array.PiRGBArray(self._camera)
        self.auto_awb = auto_awb
        self.awb_gains = awb_gains
        # self.downsize = downsize
        # self.resolution = (2592, 1944)
        self.resolution = resolution

    def next_frame(self):
        # capture(output, format=None, use_video_port=False, resize=None,
        #         splitter_port=0, **options)
        # self._camera.capture(self._stream, format='bgr', resize=self.downsize)
        self._stream.truncate()
        self._stream.seek(0)
        self._camera.capture(self._stream, format="bgr")
        # pdb.set_trace()
        return self._stream.array

    # def frames()

    def frames(self):
        for i in itertools.count():
            yield from self.next_frame()

    def close(self):
        self._camera.close()

    def setup(self):
        self._camera.meter_mode = "backlit"
        self._camera.sensor_mode = 2
        if self.resolution is not None:
            self._camera.resolution = self.resolution
        # camera.framerate only affects the video port-based captures
        # self._camera.framerate = 5
        time.sleep(4)
        self._camera.shutter_speed = self._camera.exposure_speed
        log.info("Exposure speed: %s", self._camera.exposure_speed)
        log.info("Sensor mode: %s", self._camera.sensor_mode)
        awb_gains = self._camera.awb_gains
        self._camera.awb_mode = "off"
        log.info("AWB Gains: Red: %f, Blue: %f", *awb_gains)
        log.debug("Exact AWB gains: %s", str(awb_gains))
        if self.auto_awb:
            self._camera.awb_gains = awb_gains
        else:
            self._camera.awb_gains = self.awb_gains
        self._camera.image_effect = "none"
        # Disable camera gain setting
        self._camera.exposure_mode = "off"
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

    def get(self, prop):
        return getattr(self._camera, prop)


def get_camera(**kwargs):
    """
    Returns the camera object for the correct device.
    """
    if ON_PI:
        # return PiCamera(resolution=(1296, 972), downsize=(1296, 972))
        return PiCamera(**kwargs)
    return OpenCVCamera()


def main():
    """
    Image aqcuisition
    Entry point for take_pics
    """
    parser = argparse.ArgumentParser(
        "Takes pictures using picamera or OpenCV VideoCapture"
    )
    parser.add_argument(
        "-o,",
        "--output",
        help="Output to directory",
        default="/home/pi/ForwardVision/images/",
    )
    parser.add_argument(
        "-f,", "--format", help="Picture file name extension", default="jpg"
    )
    args = parser.parse_args()

    image_dir = os.path.normpath(args.output)
    if not os.path.isdir(image_dir):
        os.makedirs(image_dir)

    run_number_path = os.path.join(image_dir, "run.txt")
    if os.path.exists(run_number_path):
        with open(run_number_path, "r") as run:
            run_num = int(run.read().strip()) + 1
        log.info("Run number: %u", run_num)
    else:
        run_num = 0

    run_dir = os.path.join(image_dir, "run{:03d}".format(run_num))
    os.mkdir(run_dir)
    os.mkdir(os.path.join(run_dir, "frames"))

    log_path = os.path.join(run_dir, "camera.log")
    logging.basicConfig(
        format=FORMAT, datefmt=DATE_FMT, level=logging.DEBUG, filename=log_path
    )
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_formatter = logging.Formatter(fmt=STREAM_FORMAT, datefmt=STREAM_DATE_FMT)
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(logging.INFO)
    log.addHandler(stream_handler)

    try:
        log.info("Beginning Camera")
        camera = get_camera()
        camera.setup()
        log.info("Camera setup complete")
        with open(run_number_path, "w") as run:
            run.write(str(run_num))
            run.write("\n")
        log.info("run number=%u", run_num)
        i = 0
        start = datetime.datetime.now()
        while True:
            # now = datetime.datetime.now()
            # try:
            frame = camera.next_frame()
            # except PiCameraResolutionRounded:

            next_frame = "image{:06d}.{}".format(i, args.format)
            frame_path = os.path.join(run_dir, "frames", next_frame)
            # np.savez_compressed(frame_file, frame)
            cv2.imwrite(frame_path, frame)
            log.info("image saved: %s, size=%s", next_frame, frame.shape)
            log.info("camera brightness: %d", camera.get("brightness"))
            log.info("camera contrast: %d", camera.get("contrast"))
            log.info("camera exposure speed: %d", camera.get("exposure_speed"))
            log.info("camera iso: %d", camera.get("iso"))
            log.info("camera saturation: %d", camera.get("saturation"))

            i += 1
    except KeyboardInterrupt:
        log.info("KeybordInterrupt: shutting down...")
    finally:
        diff = datetime.datetime.now() - start
        log.info("Running for: %s", str(diff))
        log.info("FPS=%0.2f", i / diff.total_seconds())
        camera.close()


if __name__ == "__main__":
    main()
