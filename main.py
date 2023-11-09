import pyvirtualcam
import numpy as np
import cv2
import colorsys

from PIL import Image, ImageOps

CAMERA_ID = 0
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

BOX_WIDTH = 384
BOX_HEIGHT = 216

TINT_INTENSITY = 0.2
BORDER_WIDTH = 2

hue = 0
hue_speed = 0.01  # per second
hue_step = 0.3

x = 0
y = 0
speed = 100  # pixels per second

direction_x = 1
direction_y = 1

with pyvirtualcam.Camera(width=WIDTH, height=HEIGHT, fps=20, device=DEVICE_PATH) as cam:
    print(f'Using virtual camera: {cam.device}')
    while True:
        # Move box
        delta_s = 1 / cam.current_fps
        x += direction_x * delta_s * speed
        y += direction_y * delta_s * speed

        x_other = x + BOX_WIDTH
        y_other = y + BOX_HEIGHT

        if x > WIDTH or x < 0 or x_other > WIDTH or x_other < 0:
            direction_x *= -1
            hue = (hue + hue_step) % 1.0
        if y > HEIGHT or y < 0 or y_other > HEIGHT or y_other < 0:
            direction_y *= -1
            hue = (hue + hue_step) % 1.0

        # Change hue
        # hue += (hue_speed * delta_s) % 1.0
        tint_color = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue, 1, 1))
        # LSP gets mad if I don't do this
        tint_color = (tint_color[0], tint_color[1], tint_color[2], 255)

        # Frame stuff
        ret, frame = vc.read()
        if not ret:
            raise RuntimeError('Error fetching frame')

        # BGR => RGB
        frame = frame[...,::-1]
        image = Image.fromarray(frame)
        image = image.convert('RGBA')
        # Create box
        image = image.resize((BOX_WIDTH, BOX_HEIGHT))
        color_layer = Image.new('RGBA', (BOX_WIDTH, BOX_HEIGHT), tint_color)
        image = Image.blend(image, color_layer, TINT_INTENSITY)

        background = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255))

        border = Image.new('RGBA', (WIDTH - BORDER_WIDTH * 2, HEIGHT - BORDER_WIDTH * 2), (0, 0, 0, 0))
        border = ImageOps.expand(border, border=BORDER_WIDTH, fill=tint_color)

        background.paste(image, (round(x), round(y)))
        background.alpha_composite(border, (0, 0))

        result = np.array(background)
        result = result[:, :, :3]
        cam.send(result)
        cam.sleep_until_next_frame()
