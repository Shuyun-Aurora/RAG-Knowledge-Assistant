from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from controller import PostController, ExerciseController
from controller import LoginController
from controller import UserController
from controller import CourseController

from controller import rag_controller, knowledge_graphController
from controller.rag_controller import router as rag_router
from controller.knowledge_graphController import router as knowledge_graph_router
from config.settings import settings
from repository.embedding_repository import QwenEmbeddings
from repository.llm_repository import DeepSeekLLM
from repository.document_repository import DocumentRepository
from repository.document_parser_repository import DocumentParserRepository
from dao.vector_dao import VectorDAO
from dao.document_dao import DocumentDAO
from dao.chat_history_dao import ChatHistoryDAO
from dao.knowledge_graph_dao import KnowledgeGraphDAO
from repository.chat_history_repository import ChatHistoryRepository
from service.rag_service import RAGService
from service.knowledge_graph_service import KnowledgeGraphService


import os
from dotenv import load_dotenv

from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from util.exception import http_exception_handler, validation_exception_handler


# 1. 加载 .env 文件
load_dotenv()

# 2. 从环境变量读取 secret_key
secret_key = os.getenv("SESSION_SECRET_KEY")

# 3. 初始化 app
app = FastAPI()

# 允许的前端地址可通过 CORS_ALLOWED_ORIGINS 配置，多个值用逗号分隔
default_origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://127.0.0.1:3000",
]
cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
origins = [
    origin.strip()
    for origin in cors_origins_env.split(",")
    if origin.strip()
] or default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,   
    allow_credentials=True, # 允许的来源
    allow_methods=["*"],              # 允许所有方法
    allow_headers=["*"],              # 允许所有请求头
)

#注册你的路由
app.include_router(LoginController.router, prefix="/api")
app.include_router(UserController.router, prefix="/api/user")
app.include_router(CourseController.router, prefix="/api/course")
app.include_router(PostController.router, prefix="/api/course")
app.include_router(ExerciseController.router)  # 移除prefix="/api"因为在controller中已经定义了

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

embedding = QwenEmbeddings(settings.DASHSCOPE_API_KEY)
llm = DeepSeekLLM(settings.DEEPSEEK_API_KEY)

# 初始化Repository层（直接和数据库交互）
document_repository = DocumentRepository()
document_parser_repository = DocumentParserRepository(settings.DASHSCOPE_API_KEY)

# 初始化DAO层（作为service和repository之间的桥梁）
vector_dao = VectorDAO(embedding=embedding, db_path="./chroma_db")
document_dao = DocumentDAO(document_repository=document_repository, document_parser_repository=document_parser_repository)

# 1. 实例化 repository
chat_history_repository = ChatHistoryRepository(settings.MONGODB_URI, settings.MONGODB_DB)
# 2. 实例化 dao
chat_history_dao = ChatHistoryDAO(chat_history_repository)

# 初始化知识图谱DAO
knowledge_graph_dao = KnowledgeGraphDAO(
    neo4j_uri=settings.NEO4J_URI,
    neo4j_user=settings.NEO4J_USER,
    neo4j_password=settings.NEO4J_PASSWORD
)

# 初始化Service层（只通过DAO层和repository交互）
knowledge_graph_service = KnowledgeGraphService(knowledge_graph_dao, vector_dao)
rag_service = RAGService(vector_dao, llm, document_dao, chat_history_dao, knowledge_graph_service)

# 注入到 controller 层
rag_controller.rag_service = rag_service
knowledge_graphController.knowledge_graph_service = knowledge_graph_service

# 注册路由
app.include_router(rag_router)
app.include_router(knowledge_graph_router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    document_repository.close()
    knowledge_graph_dao.close()  # 关闭Neo4j连接


