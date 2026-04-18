#!/bin/bash
echo "🚀 正在启动后端服务..."

# === 让 conda 命令在脚本中生效 ===
source /root/miniconda3/etc/profile.d/conda.sh
conda activate rag

cd /root/RAG-Knowledge-Assistant/Code/backend

PID_UVICORN=$(ps -ef | grep "uvicorn main:app" | grep -v grep | awk '{print $2}')
if [ -n "$PID_UVICORN" ]; then
  kill -9 $PID_UVICORN
  echo "✅ 已结束旧的 FastAPI 进程: $PID_UVICORN"
fi

PID_CELERY=$(ps -ef | grep "celery -A util.celery_app worker" | grep -v grep | awk '{print $2}')
if [ -n "$PID_CELERY" ]; then
  kill -9 $PID_CELERY
  echo "✅ 已结束旧的 Celery 进程: $PID_CELERY"
fi

# 安装依赖
# pip install -r requirements.txt

nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
echo "🚀 FastAPI 后端已启动"

nohup celery -A util.celery_app worker -P solo --loglevel=info > celery.log 2>&1 &
echo "⚙️ Celery Worker 已启动"

echo "✅ 全部启动完成"