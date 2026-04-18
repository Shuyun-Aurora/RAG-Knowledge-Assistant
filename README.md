# RAG-Knowledge-Assistant 部署说明

本文档面向第一次接手本项目的同学，按步骤完成即可在本地启动项目。

## 1. 准备工作

建议直接使用 VS Code 打开项目根目录：

```text
E:\RAG-Knowledge-Assistant
```

本地需要提前安装：

- Node.js
- Conda
- MySQL + MySQL Workbench
- MongoDB
- Neo4j Desktop 或其他可本地启动 Neo4j 的方式

## 2. 项目结构

- 前端目录：`Code/frontend`
- 后端目录：`Code/backend`
- MySQL 导入文件：`File/Dump20260418.sql`

## 3. 前端部署

### 3.1 安装前端依赖

在 VS Code 终端中执行：

```powershell
cd E:\RAG-Knowledge-Assistant\Code\frontend
npm install
```

### 3.2 检查前端环境变量

先从 `Code/frontend/.env.example` 复制一份，命名为 `Code/frontend/.env`。

前端通常保持默认即可，内容如下：

```env
REACT_APP_BASE_URL=http://127.0.0.1:8000
```

### 3.3 启动前端

```powershell
cd E:\RAG-Knowledge-Assistant\Code\frontend
npm start
```

启动成功后，前端默认地址通常为：

```text
http://localhost:3000
```

## 4. 数据库准备

### 4.1 MySQL 导入

本项目的 MySQL 数据库需要先导入初始化 SQL。

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
6. 如果你想改成其他数据库名，也可以先自行修改 SQL 文件中的建库语句和相关库名，再执行导入
7. 点击 `Start Import`

### 4.2 Neo4j 启动

本项目的知识图谱功能依赖 Neo4j。

请先确保 Neo4j 已经在本机启动，并且能够正常访问。  
默认配置通常为：

```env
NEO4J_URI=neo4j://localhost:7687
```

如果你使用的是 Neo4j Desktop，看到数据库实例处于运行状态即可。

## 5. 后端部署

### 5.1 创建并激活 conda 环境

推荐使用 Python 3.11：

```powershell
conda create -n rag python=3.11 -y
conda activate rag
```

如果你已经有 `rag` 环境，直接激活即可：

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

然后按自己的本地环境修改密码、API key 等值。需要填写这些项目：

- `MYSQL_PASSWORD`
- `MYSQL_DB`
- `NEO4J_PASSWORD`
- `DASHSCOPE_API_KEY`
- `DEEPSEEK_API_KEY`

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

建议每次按下面顺序启动：

1. 打开 VS Code 项目
2. 启动前端
3. 确认 MySQL 已导入并可用
4. 启动 Neo4j
5. 激活 `rag` 环境
6. 启动后端

## 7. 一套最常用的启动命令

### 前端

```powershell
cd E:\RAG-Knowledge-Assistant\Code\frontend
npm install
npm start
```

### 后端

```powershell
conda activate rag
cd E:\RAG-Knowledge-Assistant\Code\backend
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```
