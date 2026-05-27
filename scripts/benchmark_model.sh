#!/bin/bash
# 模型推理速度测试（通过命令行参数指定模型）
# 用法: ./benchmark_model.sh [模型名] [测试消息] [生成token数]

MODEL="${1:-qwen3:4b}"
TEST_MSG="${2:-你好，请简单介绍一下自己。}"
NUM_PREDICT="${3:-64}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="$PROJECT_ROOT/assistants/chat-assistant/venv-chat/bin/python3"
WARMUP=2
BENCH=5

echo "模型: $MODEL | 最大 token: $NUM_PREDICT"

$VENV_PYTHON << PYEOF
import time, requests, os
model = os.environ.get('MODEL', 'qwen3:4b')
msg = os.environ.get('TEST_MSG', '你好')
num_predict = int(os.environ.get('NUM_PREDICT', 64))
url = "http://localhost:11434/api/chat"
warmup = int(os.environ.get('WARMUP', 2))
bench = int(os.environ.get('BENCH', 5))

def test_round():
    t0 = time.time()
    r = requests.post(url, json={
        "model": model,
        "messages": [{"role": "user", "content": msg}],
        "stream": False,
        "options": {"num_predict": num_predict, "temperature": 0.7}
    }, timeout=60)
    t = time.time() - t0
    resp = r.json()
    tokens = resp.get("eval_count", 0)
    return t, tokens

print(f"预热 {warmup} 轮...")
for i in range(warmup):
    dur, tok = test_round()
    print(f"  预热 {i+1}: {dur:.2f}s, {tok} tokens, {tok/dur:.1f} tok/s" if tok > 0 else f"  预热 {i+1}: 无输出")

print(f"\n正式测试 {bench} 轮...")
total_time, total_tokens = 0, 0
for i in range(bench):
    dur, tok = test_round()
    total_time += dur
    total_tokens += tok
    rate = tok/dur if dur > 0 else 0
    print(f"  第{i+1}轮: {dur:.2f}s, {tok} tokens, {rate:.1f} tok/s")

print(f"\n平均: {total_time/bench:.2f}s, {total_tokens/bench:.0f} tokens, {total_tokens/total_time:.1f} tok/s")
PYEOF
