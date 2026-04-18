# RAG-Knowledge-Assistant 本地部署说明

本文档对应测试作业精简版分支，当前项目仅保留课程平台的基础功能：

- 用户注册、登录、个人信息
- 课程创建、浏览、加入、退出、解散
- 课程资料上传、查看、下载、PDF 预览、删除
- 练习题上传、查看、作答、删除
- 课程社区发帖、评论、回复

当前版本不再依赖 Neo4j、MongoDB、DashScope、DeepSeek，也不包含知识图谱、智能问答、习题推送等功能。

## 1. 准备工作

建议直接使用 VS Code 打开项目根目录：

```text
E:\RAG-Knowledge-Assistant
```

本地需要提前安装：

- Node.js
- Conda
- MySQL
- MySQL Workbench

## 2. 项目结构

- 前端目录：`Code/frontend`
- 后端目录：`Code/backend`
- MySQL 导入文件：`File/Dump20260418.sql`

## 3. 前端部署

### 3.1 安装前端依赖

```powershell
cd E:\RAG-Knowledge-Assistant\Code\frontend
npm install
```

### 3.2 配置前端环境变量

先从 `Code/frontend/.env.example` 复制一份，命名为 `Code/frontend/.env`。

默认内容如下：

```env
REACT_APP_BASE_URL=http://127.0.0.1:8000
```

### 3.3 启动前端

```powershell
cd E:\RAG-Knowledge-Assistant\Code\frontend
npm start
```

启动成功后，前端地址通常为：

```text
http://localhost:3000
```

## 4. 数据库准备

### 4.1 MySQL 导入

SQL 文件位置：

```text
File/Dump20260418.sql
```

在 MySQL Workbench 中操作：

1. 打开顶部菜单 `Server -> Data Import`
2. 选择 `Import from Self-Contained File`
3. 选择项目中的 SQL 文件：`File/Dump20260418.sql`
4. `Default Target Schema` 可以不用修改，因为这个 SQL 文件里已经写了建库语句
5. SQL 中默认创建的数据库名为：`rag_db`
6. 如果想改成其他数据库名，也可以先自行修改 SQL 文件中的建库语句和相关库名，再执行导入
7. 点击 `Start Import`

## 5. 后端部署

### 5.1 创建并激活 conda 环境

推荐使用 Python 3.11：

```powershell
conda create -n rag python=3.11 -y
conda activate rag
```

如果已经有 `rag` 环境，直接激活即可：

```powershell
conda activate rag
```

### 5.2 安装后端依赖

```powershell
cd E:\RAG-Knowledge-Assistant\Code\backend
pip install -r requirements.txt
```

### 5.3 填写后端环境变量

先从 `Code/backend/.env.example` 复制一份，命名为 `Code/backend/.env`。

确认文件 `Code/backend/.env` 已正确填写。至少需要填写这些项目：

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DB`
- `JWT_SECRET_KEY`

### 5.4 启动后端

```powershell
cd E:\RAG-Knowledge-Assistant\Code\backend
uvicorn main:app --host 127.0.0.1 --port 8000
```

启动成功后，后端地址为：

```text
http://127.0.0.1:8000
```

## 6. 推荐启动顺序

1. 使用 VS Code 打开项目
2. 导入并确认 MySQL 数据库可用
3. 启动前端
4. 激活 `rag` 环境
5. 启动后端
