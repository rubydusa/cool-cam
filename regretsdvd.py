import pyvirtualcam
import numpy as np
import cv2
import colorsys

from PIL import Image, ImageOps 
from time import sleep

CAMERA_1_ID = 0
CAMERA_2_ID = 2
DEVICE_PATH = '/dev/video5'

vc1 = cv2.VideoCapture(CAMERA_1_ID)
vc2 = cv2.VideoCapture(CAMERA_2_ID)

pref_width = 1280
pref_height = 720
pref_fps_in = 30
vc1.set(cv2.CAP_PROP_FRAME_WIDTH, pref_width)
vc1.set(cv2.CAP_PROP_FRAME_HEIGHT, pref_height)
vc1.set(cv2.CAP_PROP_FPS, pref_fps_in)

# Query final capture device values (may be different from preferred settings).
WIDTH = int(vc1.get(cv2.CAP_PROP_FRAME_WIDTH))
HEIGHT = int(vc1.get(cv2.CAP_PROP_FRAME_HEIGHT))
FPS = vc1.get(cv2.CAP_PROP_FPS)

BOX_WIDTH = 384
BOX_HEIGHT = 216

TINT_INTENSITY = 0.2
BORDER_WIDTH = 2

hue = 0
hue_speed = 0.02  # per second
hue_step = 0.0

x = 0
y = 0
speed = 100  # pixels per second

direction_x = 1
direction_y = 1

background_image = None

with pyvirtualcam.Camera(width=WIDTH, height=HEIGHT, fps=20, device=DEVICE_PATH) as cam:
    background = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))
    first_cap = np.array(background)[:, :, :3]
    cam.send(first_cap)
    cam.sleep_until_next_frame()

    for i in range(10):
        print(10 - i)
        sleep(1)

    print(f'Using virtual camera: {cam.device}')
    while True:
        # Move box
        delta_s = 1 / cam.current_fps
        prev_x = x
        prev_y = y
        x += direction_x * delta_s * speed
        y += direction_y * delta_s * speed

        x_other = x + BOX_WIDTH
        y_other = y + BOX_HEIGHT

        x_flipped = x > WIDTH or x < 0 or x_other > WIDTH or x_other < 0
        y_flipped = y > HEIGHT or y < 0 or y_other > HEIGHT or y_other < 0

        if x_flipped:
            direction_x *= -1
        if y_flipped:
            direction_y *= -1

        if x > WIDTH:
            x = WIDTH
        if x < 0:
            x = 0
        if x_other > WIDTH:
            x = WIDTH - BOX_WIDTH
        if x_other < 0:
            x = BOX_WIDTH
        if y > HEIGHT:
            y = HEIGHT
        if y < 0:
            y = 0
        if y_other > HEIGHT:
            y = HEIGHT - BOX_HEIGHT
        if y_other < 0:
            y = BOX_HEIGHT

        x_other = x + BOX_WIDTH
        y_other = y + BOX_HEIGHT

        # Change hue
        hue += (hue_speed * delta_s) % 1.0
        tint_color = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1, 1))
        # LSP gets mad if I don't do this
        tint_color = (tint_color[0], tint_color[1], tint_color[2], 255)

        ret1, frame1 = vc1.read()
        if not ret1:
            raise RuntimeError('Error fetching frame')

        ret2, frame2 = vc2.read()
        if not ret2:
            raise RuntimeError('Error fetching frame')

        # BGR => RGB
        frame1 = frame1[...,::-1]
        frame2 = frame2[...,::-1]
        image1 = Image.fromarray(frame1).convert("RGBA")
        image2 = Image.fromarray(frame2).resize(image1.size).convert("RGBA")

        # Create box
        image = Image.blend(image1, image2, 0).resize((BOX_WIDTH, BOX_HEIGHT))
        color_layer = Image.new('RGBA', (BOX_WIDTH, BOX_HEIGHT), tint_color)
        image = Image.blend(image, color_layer, TINT_INTENSITY)

        background = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255)) if background_image is None else background_image

        border = Image.new('RGBA', (WIDTH - BORDER_WIDTH * 2, HEIGHT - BORDER_WIDTH * 2), (0, 0, 0, 0))
        border = ImageOps.expand(border, border=BORDER_WIDTH, fill=tint_color)

        background.paste(image, (round(x), round(y)))
        background.alpha_composite(border, (0, 0))

        if background_image is None:
            background_image = background

        final = background_image.copy()
        result = np.array(final)[:, :, :3]
        cam.send(result)
        cam.sleep_until_next_frame()
