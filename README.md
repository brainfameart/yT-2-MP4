# YouTube → MP4

A small Flask web app with a browser UI: paste a YouTube link, pick a
quality, hit Convert, download the resulting MP4.

## How to run on GitHub Codespaces (recommended)

1. Create a new repo on GitHub (can be private) and upload all the files
   from this zip into it — make sure `.devcontainer/devcontainer.json`
   ends up at `<repo>/.devcontainer/devcontainer.json`.
2. On the repo page, click the green **Code** button → **Codespaces** tab
   → **Create codespace on main**.
3. Wait for it to build (installs Python, ffmpeg, and pip packages
   automatically — takes ~1-2 minutes the first time).
4. Once the terminal opens, run:
   ```bash
   python app.py
   ```
5. A popup will appear saying a port (8080) is available — click
   **Open in Browser**. That's your UI.

Every time you reopen the Codespace later, steps 2-5 repeat (no reinstall
needed unless you deleted the Codespace).

## How to run on Replit instead

1. Create a Python Repl and upload these files (`.replit` and
   `replit.nix` need to sit at the repo root).
2. Click **Run**. If dependencies ever fail to load automatically, run
   manually in the Shell tab:
   ```bash
   pip install -r requirements.txt --break-system-packages
   python3 app.py
   ```

## How to run locally instead

```bash
pip install -r requirements.txt
# make sure ffmpeg is installed on your system:
#   macOS:   brew install ffmpeg
#   Ubuntu:  sudo apt install ffmpeg
#   Windows: https://ffmpeg.org/download.html
python app.py
```

Then open http://localhost:8080 in your browser.

## Notes

- Downloaded files are temporarily stored in `downloads/<job_id>/` and
  auto-cleaned after an hour.
- Only convert videos you own or have explicit permission to download.
  Downloading copyrighted content without authorization can violate
  YouTube's Terms of Service and copyright law.
