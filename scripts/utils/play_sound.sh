#!/bin/bash

# --- 聲音檔案路徑設定 ---
# macOS 系統音效路徑
SOUND_FILE="/System/Library/Sounds/Glass.aiff"

# --- 跨平台播放指令 ---
# 偵測當前的作業系統
OS="$(uname)"

case "$OS" in
  # macOS
  "Darwin")
    # afplay 是 macOS 內建的指令
    afplay "$SOUND_FILE"
    ;;
  # Linux
  "Linux")
    # paplay (PulseAudio) 或 aplay (ALSA) 是 Linux 常用的指令
    if command -v paplay &> /dev/null; then
      paplay "$SOUND_FILE"
    elif command -v aplay &> /dev/null; then
      aplay "$SOUND_FILE"
    else
      echo "在您的 Linux 系統上找不到 paplay 或 aplay 指令。" >&2
    fi
    ;;
  # Windows (透過 Git Bash 或 WSL)
  *)
    echo "此 .sh 腳本不完全支援您的作業系統 ($OS)。" >&2
    ;;
esac