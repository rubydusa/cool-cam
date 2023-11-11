import pyvirtualcam
import numpy as np
import cv2
import colorsys
import math

from PIL import Image, ImageOps, ImageDraw, ImageFont

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
hue_speed = 0.02  # per second
# hue_step = 0.3
hue_step = 0.0

x = 0
y = 0
speed = 100  # pixels per second

direction_x = 1
direction_y = 1

background_image = None

def dis(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]

    return math.sqrt(dx ** 2 + dy ** 2)

lowest_tl = 10000
lowest_tr = 10000
lowest_bl = 10000
lowest_br = 10000

with pyvirtualcam.Camera(width=WIDTH, height=HEIGHT, fps=20, device=DEVICE_PATH) as cam:
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

        if x_flipped or y_flipped:
            speed *= 1.01
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

        # if x > WIDTH or x < 0 or x_other > WIDTH or x_other < 0:
        #     x = prev_x
        #     direction_x *= -1
        #     hue = (hue + hue_step) % 1.0
        #     speed *= 1.01
        # if y > HEIGHT or y < 0 or y_other > HEIGHT or y_other < 0:
        #     y = prev_y
        #     direction_y *= -1
        #     hue = (hue + hue_step) % 1.0
        #     speed *= 1.01

        # Change hue
        hue += (hue_speed * delta_s) % 1.0
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

        background = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 255)) if background_image is None else background_image

        border = Image.new('RGBA', (WIDTH - BORDER_WIDTH * 2, HEIGHT - BORDER_WIDTH * 2), (0, 0, 0, 0))
        border = ImageOps.expand(border, border=BORDER_WIDTH, fill=tint_color)

        background.paste(image, (round(x), round(y)))
        background.alpha_composite(border, (0, 0))

        if background_image is None:
            background_image = background

        final = background_image.copy()
        draw = ImageDraw.Draw(final)
        font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 30)
        
        tl_dis = dis((x, y), (0, 0))
        tr_dis = dis((x_other, y), (WIDTH, 0))
        bl_dis = dis((x, y_other), (0, HEIGHT))
        br_dis = dis((x_other, y_other), (WIDTH, HEIGHT))
        lowest_tl = min(lowest_tl, tl_dis)
        lowest_tr = min(lowest_tr, tr_dis)
        lowest_bl = min(lowest_bl, bl_dis)
        lowest_br = min(lowest_br, br_dis)

        text = f"tl: x: {x:.2f}, y: {y:.2f}, d: {tl_dis:.2f}, m: {lowest_tl}"
        draw.text((16, 16), text, font=font, fill=(255, 255, 255), stroke_fill=(0, 0, 0), stroke_width=2)
        text = f"tr: x: {x_other:.2f}, y: {y:.2f}, d: {tr_dis:.2f}, m: {lowest_tr}"
        draw.text((16, 16 + 32), text, font=font, fill=(255, 255, 255), stroke_fill=(0, 0, 0), stroke_width=2)
        text = f"bl: x: {x:.2f}, y: {y_other:.2f}, d: {bl_dis:.2f}, m: {lowest_bl}"
        draw.text((16, 16 + 64), text, font=font, fill=(255, 255, 255), stroke_fill=(0, 0, 0), stroke_width=2)
        text = f"br: x: {x_other:.2f}, y: {y_other:.2f}, d: {br_dis:.2f}, m: {lowest_br}"
        draw.text((16, 16 + 96), text, font=font, fill=(255, 255, 255), stroke_fill=(0, 0, 0), stroke_width=2)

        result = cv2.flip(np.array(final), 1)
        result = result[:, :, :3]
        cam.send(result)
        cam.sleep_until_next_frame()
