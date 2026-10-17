import shutil
import subprocess
import uuid
from pathlib import Path

import db
import yt_dlp

MAX_FILESIZE = 200 * 1024 * 1024  # 200 MB

VIDEO_WIDTH, VIDEO_HEIGHT = 256, 144


def shrink(src: Path, dst: Path):
    subprocess.run([
        "ffmpeg", "-loglevel", "error", "-y", # dont rpint banner, plus no confirmations (yes)
        "-i", str(src), #input file
        "-vf", (
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT}"
        ), # video filters.
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", # -> H.264
        "-c:a", "copy", # dont touch the audio
        str(dst),
    ], check=True) # Actually catch subprocess failures.


def download_video(url: str) -> str:
    name = uuid.uuid4().hex
    opts = {
        "format": "bv*[height<=360]+ba/b[height<=360]/wv*+ba/w", # best video+audio up to 360p
        "format_sort": ["vcodec:h264"], # prefer H.264
        "merge_output_format": "mkv",
        "outtmpl": str(db.incoming_dir() / f"{name}.%(ext)s"), # save as incoming/<uuid>.<ext>
        "noplaylist": True, # just the one video
        "max_filesize": MAX_FILESIZE, # skip anything bigger
        "match_filter": yt_dlp.utils.match_filter_func("!is_live"), # no live streams
        "quiet": True, # no logs
        "noprogress": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url)
        if not info or not info.get("requested_downloads"):
            raise RuntimeError("Video was skipped (too large, or a live stream).")
        path = Path(info["requested_downloads"][0]["filepath"])  # final path after merging
        small = db.incoming_dir() / f"{name}.small.mkv"
        shrink(path, small)
        shutil.move(small, db.videos_dir() / f"{name}.mkv")
        return f"{name}.mkv"
    finally:
        for leftover in db.incoming_dir().glob(f"{name}*"):
            leftover.unlink()
