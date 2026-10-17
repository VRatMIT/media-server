import queue
import subprocess
import threading
import time

import animations
import db
from download import VIDEO_HEIGHT
from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions

FPS = 60

def full_matrix():
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 4
    options.parallel = 3
    options.pixel_mapper_config = "" # mostly useless, was useful a while ago
    options.hardware_mapping = "regular"
    options.gpio_slowdown = 3
    options.pwm_bits = 9
    options.brightness = 100
    options.drop_privileges = False # possibly remove
    return RGBMatrix(options=options)

def start_ffmpeg(video_path, width, height):
    video_filters = (
        f"fps={FPS},"
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height}"
    )
    cmd = [
        "ffmpeg", "-loglevel", "error",
        "-i", video_path,
        "-an",
        "-vf", video_filters,
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-threads", "2",
        "-", # pipe to stdout
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**7)

# Read frame from ffmpeg process and return the image bytes.
def read_frame(proc, width, height) -> Image:
    frame_size = width * height * 3
    raw = proc.stdout.read(frame_size)
    if len(raw) < frame_size: # not enough bytes means the video has ended?
        return None
    return Image.frombytes("RGB", (width, height), raw)

# Path of the next video in the queue, or None if it's empty
def next_video():
    while True:
        try:
            title, _ = video_queue.get_nowait()
        except queue.Empty:
            return None

        video = db.get_video(title)
        if video:
            return db.videos_dir() / video["filename"]

def clear_video_queue():
    while True:
        try:
            video_queue.get_nowait()
        except queue.Empty:
            return

stop = threading.Event()

action_queue = queue.Queue()
video_queue = queue.Queue()

state = {"power": False, "brightness": 50, "message": None}

# Apply actions queue
def apply_actions():
    while True:
        try:
            action, value = action_queue.get_nowait()
        except queue.Empty:
            return
        state[action] = value

def run():
    matrix: RGBMatrix = full_matrix()

    width, height = matrix.width, matrix.height
    video_height = VIDEO_HEIGHT  # rows below it are for text and clock

    canvas = matrix.CreateFrameCanvas()

    proc = None
    was_on = False
    anim_frame = None

    try:
        while not stop.is_set():
            frame_start = time.monotonic()
            apply_actions()

            if state["power"] != was_on:
                was_on = state["power"]
                anim_frame = 0

            off_screen = animations.off_screen(width, height, state["brightness"])

            if not state["power"] and anim_frame is None:
                if proc:
                    proc.kill()
                    proc = None
                frame = off_screen
            else:
                if proc is None and state["power"]:
                    path = next_video()
                    if path:
                        proc = start_ffmpeg(path, width, video_height)

                frame = Image.new("RGB", (width, height))

                if proc:
                    video_frame = read_frame(proc, width, video_height)
                    if video_frame:
                        frame.paste(video_frame)
                    else:
                        proc.kill()
                        proc = None

                # TODO: scrolling text and clock

                if anim_frame is not None:
                    progress = anim_frame / animations.ANIM_FRAMES
                    frame = animations.power_bars(frame, off_screen, progress, turning_on=state["power"])
                    anim_frame += 1
                    if anim_frame > animations.ANIM_FRAMES:
                        anim_frame = None

            canvas.brightness = state["brightness"]
            canvas.SetImage(frame)
            canvas = matrix.SwapOnVSync(canvas)

            stop.wait(max(0, 1 / FPS - (time.monotonic() - frame_start)))
    finally:
        if proc:
            proc.kill()
        matrix.Clear()
