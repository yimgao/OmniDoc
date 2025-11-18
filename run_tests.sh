#!/bin/bash
# 运行测试脚本 - 跳过需要数据库的测试

set -e

echo "🧪 Running OmniDoc Tests..."
echo "================================"

# 运行不需要数据库的单元测试
echo ""
echo "📦 Running unit tests (excluding database-dependent tests)..."
uv run pytest tests/unit/test_cross_referencer.py \
           tests/unit/test_error_handler.py \
           tests/unit/test_parallel_executor.py \
           tests/unit/test_rate_limiter.py \
           -v --tb=short

echo ""
echo "📦 Running API tests..."
uv run pytest tests/test_api.py \
           tests/test_utils.py \
           tests/test_health.py \
           tests/test_monitoring.py \
           tests/test_websocket.py \
           -v --tb=short

echo ""
echo "✅ Tests completed!"
