#!/bin/bash
set -e

echo "🚀 启动前端服务..."

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 20

cd /root/RAG-Knowledge-Assistant/Code/frontend

# 安装依赖
# npm install

# 构建前端
# npm run build

# 杀掉旧的 serve 进程
PID=$(ps -ef | grep "serve -s build" | grep -v grep | awk '{print $2}')
if [ -n "$PID" ]; then
  kill -9 $PID
  echo "✅ 已结束旧的前端进程: $PID"
fi

# 启动 serve
nohup npx serve -s build -l 3000 > frontend.log 2>&1 &
echo "🚀 前端已启动"
