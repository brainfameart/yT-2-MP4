#!/usr/bin/env bash
# Auto-installs Python dependencies on first run (and every run, cheaply,
# since pip skips already-satisfied packages).
pip install -r requirements.txt --quiet --break-system-packages 2>/dev/null || \
pip install -r requirements.txt --quiet
