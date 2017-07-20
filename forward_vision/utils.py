import os
import sys


ON_PI = 'arm' in os.uname().machine

IMAGES_DIR = os.path.join(os.path.dirname(__file__), 'images')