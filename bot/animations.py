from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

ANIM_FRAMES = 60

# tv bar animations
def power_bars(frame, background, progress, turning_on):
    closed = 1 - (1 - progress) ** 3
    if turning_on:
        closed = 1 - closed

    width, height = frame.size
    bar = int(closed * height / 2)

    frame.paste(background.crop((0, 0, width, bar)), (0, 0))
    frame.paste(background.crop((0, height - bar, width, height)), (0, height - bar))
    return frame

# Scren that displays when the matrix is off
def off_screen(width, height, brightness):
    level = min(255, 255 * 5 // max(brightness, 1))
    white = (level, level, level)

    frame = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(frame)
    draw.fontmode = "1"  # disable antialias

    clock = datetime.now().strftime("%I:%M").lstrip("0")
    draw.text((width / 2, height / 2), clock, font=ImageFont.load_default(size=64), fill=white, anchor="mm")
    draw.text((width - 2, height - 2), "OFF", font=ImageFont.load_default(size=12), fill=white, anchor="rd")
    return frame
