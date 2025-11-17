#!/bin/bash
set -e

echo "🖥️ Iniciando Xvfb..."
Xvfb :99 -ac -screen 0 1280x1024x24 &
export DISPLAY=:99

# Aguarda Xvfb iniciar
sleep 2

echo "🐍 Iniciando Python..."
exec python3 capture_qr.py
