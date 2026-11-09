import queue
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import animations
import bluetooth
import db
from download import VIDEO_HEIGHT
from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions

FPS = 60
BT_AUDIO_DELAY = 1.05 # in seconds, not ms
IDLE_TIMEOUT = 43200

stop = threading.Event()

action_queue = queue.Queue()
video_queue = queue.Queue()

state = {"power": False, "brightness": 50, "message": None, "audio": False, "skip": 0}
video_state = {"title": None, "queued_by": None, "video_duration": -1, "loops_left": 0}

@dataclass
class QueuedVideo:
    title: str
    queued_by: int = 0
    queued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    loop: int = 1

@dataclass
class Playback:
    proc: subprocess.Popen
    audio_proc: subprocess.Popen
    video_frame: int
    video_start: int
    frames_read: int



def apply_actions():
    while True:
        try:
            action, value = action_queue.get_nowait()
        except queue.Empty:
            return
        
        state[action] = value


def next_video():
    while True:
        try:
            queued = video_queue.get_nowait()
        except queue.Empty:
            return None

        video = db.get_video(queued.title)
        if video:
            video_state.update(title=queued.title, queued_by=queued.queued_by, loops_left=queued.loop - 1)
            return db.videos_dir() / video["filename"]

def replay_video():
    if video_state["loops_left"] <= 0:
        return None
    video_state["loops_left"] -= 1
    video = db.get_video(video_state["title"])
    return db.videos_dir() / video["filename"] if video else None


def clear_video_queue():
    while True:
        try:
            video_queue.get_nowait()
        except queue.Empty:
            return

# ====== Matrix Setup ======

def full_matrix():
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 4
    options.parallel = 3
    options.pixel_mapper_config = ""
    options.hardware_mapping = "regular"    
    options.gpio_slowdown = 3
    options.pwm_bits = 9
    options.brightness = 100
    options.drop_privileges = False
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
        "-",
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**7)


def get_duration(video_path):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video_path)],
            capture_output=True, text=True, timeout=10, check=True).stdout
        return float(out)
    except (subprocess.SubprocessError, ValueError, OSError):
        return -1


def start_audio(video_path):
    cmd = [
        "ffmpeg", "-loglevel", "error",
        "-i", video_path,
        "-vn",
        "-f", "alsa", f"bluealsa:DEV={bluetooth.speaker()}",
    ]
    return subprocess.Popen(cmd)


def read_frame(proc, width, height) -> Image:
    frame_size = width * height * 3
    raw = proc.stdout.read(frame_size)
    if len(raw) < frame_size:
        return None
    return Image.frombytes("RGB", (width, height), raw)


def kill(proc):
    if proc:
        proc.kill()
    return None


def catch_up(proc, video_frame, frames_read, target, width, height):
    while frames_read < target:
        video_frame = read_frame(proc, width, height)
        frames_read += 1
        if video_frame is None:
            break
    return video_frame, frames_read


# === Main functions ===
def handle_skips(pb: Playback) -> None:
    if state["skip"]:
        if pb.proc:
            pb.proc = kill(pb.proc)
            pb.audio_proc = kill(pb.audio_proc)
            for _ in range(state["skip"] - 1):
                next_video()
            video_state["loops_left"] = 0
        state["skip"] = 0

def check_timeout(pb: Playback, idle: float):
    if state["power"] and pb.proc is None:
        if time.monotonic() - idle > IDLE_TIMEOUT:
            state["power"] = False
    else:
        idle = time.monotonic()

# -=== Main loop ===

def run():
    matrix: RGBMatrix = full_matrix()
    width, height = matrix.width, matrix.height
    canvas = matrix.CreateFrameCanvas()

    proc = None
    audio_proc = None
    video_frame = None
    was_on = False
    anim_frame = None
    prev_off_state = None
    idle_since = time.monotonic()

    try:
        while not stop.is_set():
            frame_start = time.monotonic()
            apply_actions()

            if state["skip"]:
                if proc:
                    proc = kill(proc)
                    audio_proc = kill(audio_proc)
                    for _ in range(state["skip"] - 1):
                        next_video()
                    video_state["loops_left"] = 0
                state["skip"] = 0

            if state["power"] and proc is None:
                if time.monotonic() - idle_since > IDLE_TIMEOUT:
                    state["power"] = False
            else:
                idle_since = time.monotonic()

            if state["power"] != was_on:
                was_on = state["power"]
                anim_frame = 0

            off_state = (state["brightness"], time.strftime("%H:%M"))
            if off_state != prev_off_state:
                prev_off_state = off_state
                off_screen = animations.off_screen(width, height, state["brightness"])

            if not state["power"] and anim_frame is None:
                proc = kill(proc)
                video_state["loops_left"] = 0
                frame = off_screen
            else:
                if proc is None and state["power"]:

                    path = replay_video()
                    if not path:
                        path = next_video()
                        
                    if path:
                        video_state["video_duration"] = get_duration(path)
                        proc = start_ffmpeg(path, width, VIDEO_HEIGHT)
                        if state["audio"]:
                            audio_proc = start_audio(path)
                        video_start = time.monotonic() + (BT_AUDIO_DELAY if state["audio"] else 0)
                        frames_read = 0

                frame = Image.new("RGB", (width, height))

                if proc and time.monotonic() >= video_start:
                    target = int((time.monotonic() - video_start) * FPS) + 1
                    video_frame, frames_read = catch_up(
                        proc, video_frame, frames_read, target, width, VIDEO_HEIGHT
                    )
                    if video_frame is None:
                        proc = kill(proc)
                    else:
                        frame.paste(video_frame)

                if state["power"]:
                    animations.draw_bottom_bar(frame, state["message"])
                    duration = video_state["video_duration"]
                    playing = proc and time.monotonic() >= video_start and duration > 0
                    percent = (time.monotonic() - video_start) / duration if playing else 0
                    animations.draw_progress_bar(frame, 144, min(max(percent, 0), 1))
                    animations.draw_media_name(frame, 148, video_state["title"])

                if anim_frame is not None:
                    progress = anim_frame / animations.ANIM_FRAMES
                    frame = animations.power_bars(frame, off_screen, progress, turning_on=state["power"])
                    anim_frame += 1
                    if anim_frame > animations.ANIM_FRAMES:
                        anim_frame = None

            if proc is None or not state["audio"]:
                audio_proc = kill(audio_proc)

            canvas.brightness = state["brightness"]
            canvas.SetImage(frame)
            canvas = matrix.SwapOnVSync(canvas)

            stop.wait(max(0, 1 / FPS - (time.monotonic() - frame_start)))

    finally:
        kill(proc)
        kill(audio_proc)
        matrix.Clear()
