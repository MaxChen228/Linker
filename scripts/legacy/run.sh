#!/usr/bin/env bash
set -euo pipefail

# One-line launcher for Linker web
# Usage: ./scripts/legacy/run.sh (建議使用 ./linker.sh start)

PROJECT_DIR="$(cd "$(dirname "$0")/../../" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python3"

# 1) Ensure Python3
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ Python3 未安裝" >&2
  exit 1
fi

# 2) Ensure venv
if [ ! -d "$VENV_DIR" ]; then
  echo "📦 建立虛擬環境..."
  python3 -m venv "$VENV_DIR"
fi

# 3) Install deps via venv Python
echo "📚 安裝依賴..."
"$PYTHON_BIN" -m pip install -q -r "$PROJECT_DIR/requirements.txt"

# 4) Load API key from .env if present; otherwise use current env
ENV_FILE="$PROJECT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC2046
  export $(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$ENV_FILE" | xargs)
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "⚠️  未設定 GEMINI_API_KEY，將以備援模式啟動（不影響頁面瀏覽，但 AI 批改不可用）"
fi

# 5) Start uvicorn using venv Python (module mode avoids PATH issues)
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
echo "🚀 啟動 Web 服務於 http://${HOST}:${PORT}"
exec "$PYTHON_BIN" -m uvicorn web.main:app --host "$HOST" --port "$PORT" --log-level info


