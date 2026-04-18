# CI/CD 自动化部署配置文档

本文档说明如何在 **GitHub Actions** 上配置自动化部署，实现前后端一键部署到远程服务器。

---

## 一、系统架构概览

* **代码托管平台**：GitHub
* **部署服务器**：Linux（Ubuntu）
* **部署方式**：通过 SSH 连接服务器执行部署脚本
* **触发条件**：向 `main` 分支推送代码时自动触发
* **服务器上项目路径**：`/root/RAG-Knowledge-Assistant`

---

## 二、GitHub Secrets 配置

在 GitHub 仓库中打开
**Settings → Secrets and variables → Actions → New repository secret**，
添加以下密钥：

| 名称                | 示例值            | 说明           |
| ----------------- | -------------- | ------------ |
| `SSH_HOST`        | `123.45.67.89` | 部署服务器公网 IP   |
| `SSH_USER`        | `root`         | SSH 登录用户名    |
| `SSH_PRIVATE_KEY` | ——             | 对应服务器公钥的私钥内容 |

公钥保存在服务器的 `~/.ssh/authorized_keys`。

---

## 三、CI/CD 配置文件

文件路径：

```
.github/workflows/deploy.yml
```

内容如下：

```yaml
name: 🚀 Auto Deploy Backend

on:
  push:
    branches:
      - main  

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      # 拉取仓库代码
      - name: Checkout repository
        uses: actions/checkout@v4

      # 配置 SSH
      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/deploy_id_ed25519
          chmod 600 ~/.ssh/deploy_id_ed25519
          # 配置 SSH host 简化后续命令
          cat >> ~/.ssh/config <<EOF
          Host deploy-server
            HostName ${{ secrets.SSH_HOST }}
            User ${{ secrets.SSH_USER }}
            IdentityFile ~/.ssh/deploy_id_ed25519
            StrictHostKeyChecking no
          EOF

      # 连接服务器并部署
      - name: Deploy to server
        run: |
          ssh -t deploy-server << 'EOF'
            set -e
            echo "📦 切换到项目目录"
            cd /root/RAG-Knowledge-Assistant

            echo "📥 拉取最新代码"
            git fetch origin main
            git reset --hard origin/main

            echo "💥 执行 start_backend.sh"
            bash Code/backend/start_backend.sh

            echo "💥 执行 start_frontend.sh"
            bash Code/frontend/start_frontend.sh

            echo "✅ 部署完成"
          EOF
```

---

## 四、后端启动脚本

路径：`Code/backend/start_backend.sh`

```bash
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

nohup celery -A util.celery_app worker --loglevel=info > celery.log 2>&1 &
echo "⚙️ Celery Worker 已启动"

echo "✅ 全部启动完成"
```

---

## 五、前端启动脚本

路径：`Code/frontend/start_frontend.sh`

```bash
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
```

---

## 六、项目目录结构

```
RAG-Knowledge-Assistant/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── Code/
│   ├── backend/
│   │   ├── main.py
│   │   └── start_backend.sh
│   └── frontend/
│       ├── package.json
│       └── start_frontend.sh
```

---

## 七、部署验证

1. 推送代码到 `main` 分支：

   ```bash
   git add . && git commit -m "update xxx" && git push origin main
   ```

2. 在 GitHub → **Actions** 页面查看部署日志。
   若部署成功，日志中显示：

   ```
   📦 切换到项目目录...
   📥 拉取最新代码...
   🚀 FastAPI 后端已启动...
   🚀 前端已启动...
   ✅ 部署完成
   ```