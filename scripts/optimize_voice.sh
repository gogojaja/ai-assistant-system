#!/bin/bash
echo "=== 优化语音识别模块 ==="
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="$(dirname "$SCRIPT_DIR")"

# 1. 下载 small 模型（如果不存在）
cd "$PROJECT/shared/whisper.cpp/models"
if [ ! -f ggml-small.bin ]; then
    echo "下载 ggml-small.bin (约 466 MB)..."
    curl -L -o ggml-small.bin https://github.com/ggerganov/whisper.cpp/releases/download/v1.8.2/ggml-small.bin
    if [ $? -ne 0 ]; then
        echo "GitHub 下载失败，尝试镜像..."
        curl -L -o ggml-small.bin https://mirror.nju.edu.cn/huggingface/models/ggerganov/whisper.cpp/resolve/main/ggml-small.bin
    fi
else
    echo "模型已存在，跳过下载"
fi

# 2. 修改 callback_server.py 中的模型路径和语言参数
cd "$PROJECT/shared/feishu-callback"
cp callback_server.py callback_server.py.bak

# 替换模型路径
sed -i '' 's/MODEL = WHISPER_CPP \/ "models\/ggml-base.bin"/MODEL = WHISPER_CPP \/ "models\/ggml-small.bin"/' callback_server.py

# 在 transcribe_audio 函数中添加 -l zh 参数
sed -i '' '/cmd = \[str(WHISPER_CLI), "-m", str(MODEL), "-f", file_path, "--no-timestamps"\]/a\
    cmd.insert(5, "-l"); cmd.insert(6, "zh")' callback_server.py

echo "✅ 优化完成，请重启 Flask 服务"
