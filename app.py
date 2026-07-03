#!/usr/bin/env python3
"""
YouTube -> MP4 web app (Flask + yt-dlp)

Run locally:
    pip install -r requirements.txt
    python app.py

On Replit:
    Just click "Run" — the .replit config handles setup.

IMPORTANT: Only download videos you own or have explicit rights to
download. Downloading copyrighted content without permission may
violate YouTube's Terms of Service and copyright law.
"""

import os
import re
import sys
import uuid
import threading
import time
import subprocess


def _ensure_deps():
    """Self-heal: install missing dependencies instead of crashing on import."""
    required = {"flask": "flask>=3.0.3", "yt_dlp": "yt-dlp>=2024.8.6"}
    missing = []
    for module_name, pip_spec in required.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_spec)
    if missing:
        print(f"Installing missing dependencies: {missing} ...", flush=True)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--break-system-packages", *missing]
        )


_ensure_deps()

from flask import Flask, render_template, request, jsonify, send_from_directory, abort

import yt_dlp

app = Flask(__name__)

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# In-memory job tracker: {job_id: {"status": ..., "percent": ..., "filename": ..., "error": ...}}
JOBS = {}

YOUTUBE_URL_RE = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)[\w\-]+"
)


def is_valid_youtube_url(url: str) -> bool:
    return bool(YOUTUBE_URL_RE.match(url.strip()))


def run_download(job_id: str, url: str, quality: str):
    job_dir = os.path.join(DOWNLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    def hook(d):
        if d["status"] == "downloading":
            percent_str = d.get("_percent_str", "0%").strip()
            percent_str = re.sub(r"\x1b\[[0-9;]*m", "", percent_str)  # strip ANSI codes
            try:
                JOBS[job_id]["percent"] = float(percent_str.replace("%", ""))
            except ValueError:
                pass
        elif d["status"] == "finished":
            JOBS[job_id]["status"] = "processing"

    if quality == "best":
        fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    else:
        fmt = (
            f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]"
            f"/best[height<={quality}][ext=mp4]/best"
        )

    ydl_opts = {
        "format": fmt,
        "outtmpl": os.path.join(job_dir, "%(title).100s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True,
    }

    try:
        JOBS[job_id]["status"] = "downloading"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # merged output is forced to .mp4
            base, _ = os.path.splitext(filename)
            final_name = base + ".mp4"
            JOBS[job_id]["filename"] = os.path.basename(final_name)
            JOBS[job_id]["status"] = "done"
            JOBS[job_id]["percent"] = 100
    except Exception as e:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/start", methods=["POST"])
def start_job():
    data = request.get_json(force=True)
    url = (data.get("url") or "").strip()
    quality = (data.get("quality") or "best").strip()

    if not url or not is_valid_youtube_url(url):
        return jsonify({"error": "Please enter a valid YouTube URL."}), 400

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"status": "queued", "percent": 0, "filename": None, "error": None}

    thread = threading.Thread(target=run_download, args=(job_id, url, quality), daemon=True)
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def job_status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Unknown job id"}), 404
    return jsonify(job)


@app.route("/api/download/<job_id>")
def download_file(job_id):
    job = JOBS.get(job_id)
    if not job or job.get("status") != "done" or not job.get("filename"):
        abort(404)
    job_dir = os.path.join(DOWNLOAD_DIR, job_id)
    return send_from_directory(job_dir, job["filename"], as_attachment=True)


def cleanup_old_jobs(max_age_seconds=3600):
    """Optional: periodically clear old download folders to save disk space."""
    while True:
        time.sleep(600)
        now = time.time()
        for job_id in list(JOBS.keys()):
            job_dir = os.path.join(DOWNLOAD_DIR, job_id)
            if os.path.isdir(job_dir):
                mtime = os.path.getmtime(job_dir)
                if now - mtime > max_age_seconds:
                    try:
                        for f in os.listdir(job_dir):
                            os.remove(os.path.join(job_dir, f))
                        os.rmdir(job_dir)
                        JOBS.pop(job_id, None)
                    except OSError:
                        pass


if __name__ == "__main__":
    threading.Thread(target=cleanup_old_jobs, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting server on 0.0.0.0:{port} ...", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False)
