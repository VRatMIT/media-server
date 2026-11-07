from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

ANIM_FRAMES = 60

# tv bar animations
def power_bars(frame: Image.Image, background: Image.Image, progress: float, turning_on: bool) -> Image.Image:
    closed = 1 - (1 - progress) ** 3
    if turning_on:
        closed = 1 - closed

    width, height = frame.size
    bar = int(closed * height / 2)

    frame.paste(background.crop((0, 0, width, bar)), (0, 0))
    frame.paste(background.crop((0, height - bar, width, height)), (0, height - bar))
    return frame

# Scren that displays when the matrix is off
def off_screen(width: int, height: int, brightness: int) -> Image.Image:
    level = min(255, 255 * 5 // max(brightness, 1))
    white = (level, level, level)

    frame = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(frame)
    draw.fontmode = "1"  # disable antialias

    clock = datetime.now().strftime("%I:%M").lstrip("0")
    draw.text((width / 2, height / 2), clock, font=ImageFont.load_default(size=64), fill=white, anchor="mm")
    draw.text((width - 2, height - 2), "OFF", font=ImageFont.load_default(size=24), fill=white, anchor="rd")
    return frame

def draw_clock(frame: Image.Image, anchor) -> Image.Image:
    clock = datetime.now().strftime("%I:%M").lstrip("0")
    draw = ImageDraw.Draw(frame)
    draw.fontmode = "1"  # disable antialias

    width, height = frame.size

    draw.text((width - 1, height - 1), clock, font=ImageFont.load_default(size=24), fill=(255, 255, 255), anchor=anchor)

    return frame

def draw_progress_bar(frame: Image.Image, y: int, percent: float) -> Image.Image:
    draw = ImageDraw.Draw(frame)
    x = int(255 * percent)

    # Gray progress bar
    draw.line([(0, y), (255, y)], (30, 30, 30), 3)

    # Red line
    draw.line([(0, y), (x, y)], (219, 70, 59), 3)

    # Square if needed
    if percent > 0:
        draw.rectangle([(x - 3, y - 3), (x + 3, y + 3)], (255, 255, 255))

    return frame
