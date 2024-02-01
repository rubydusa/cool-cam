import pyvirtualcam
import numpy as np
import cv2

from PIL import Image 
from math import floor

CAMERA_ID = 2
VIRTUAL_CAMERA_ID = 5
DEVICE_PATH = '/dev/video5'

vc = cv2.VideoCapture(CAMERA_ID)

pref_width = 1280
pref_height = 720
pref_fps_in = 30
vc.set(cv2.CAP_PROP_FRAME_WIDTH, pref_width)
vc.set(cv2.CAP_PROP_FRAME_HEIGHT, pref_height)
vc.set(cv2.CAP_PROP_FPS, pref_fps_in)

# Query final capture device values (may be different from preferred settings).
WIDTH = int(vc.get(cv2.CAP_PROP_FRAME_WIDTH))
HEIGHT = int(vc.get(cv2.CAP_PROP_FRAME_HEIGHT))
FPS = vc.get(cv2.CAP_PROP_FPS)

with pyvirtualcam.Camera(width=WIDTH, height=HEIGHT, fps=20, device=DEVICE_PATH) as cam:
    while True:
        # Frame stuff
        ret, frame = vc.read()
        if not ret:
            raise RuntimeError('Error fetching frame')

        # BGR => RGB
        frame = frame[...,::-1] 
        background = Image.fromarray(frame)
        background = background.convert('RGBA')

        projection = background.copy()
        projection = projection.resize((floor(frame.shape[1] / 2), floor(frame.shape[0] / 2)))

        background.paste(projection, (0, 0))

        result = np.array(background)[:, :, :3]

        cam.send(result)
        cam.sleep_until_next_frame()

