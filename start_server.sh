# 启动前后端开发环境脚本

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "🚀 启动 OmniDoc 全栈开发环境..."
echo ""

missing_dep=false
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ 未检测到 python3，请先安装 Python 3。"
    missing_dep=true
fi

if ! command -v pnpm >/dev/null 2>&1; then
    echo "❌ 未检测到 pnpm，请执行 'npm install -g pnpm' 或 'corepack enable pnpm'。"
    missing_dep=true
fi

if [ "$missing_dep" = true ]; then
    exit 1
fi

check_port () {
    local port="$1"
    if lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "⚠️  端口 $port 已被占用"
    echo "   正在运行的进程:"
        lsof -ti:"$port" | xargs ps -p
    echo ""
    read -p "是否要停止现有进程并重新启动? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🛑 停止端口 $port 的进程..."
            lsof -ti:"$port" | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo "❌ 取消启动"
        exit 1
    fi
fi
}

check_port 8000
check_port 3000

cleanup () {
    echo ""
    echo "🧹 清理进程..."
    if [[ -n "${BACKEND_PID:-}" ]]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [[ -n "${FRONTEND_PID:-}" ]]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT

echo "✅ FastAPI 开发服务:      http://localhost:8000"
echo "✅ Next.js 前端开发服务:  http://localhost:3000"
echo "   按 Ctrl+C 可同时停止两端服务"
echo ""

python3 backend/uvicorn_dev.py &
BACKEND_PID=$!

pnpm --dir frontend dev &
FRONTEND_PID=$!

wait -n
