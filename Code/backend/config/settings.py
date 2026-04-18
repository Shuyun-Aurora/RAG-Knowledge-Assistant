from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # MySQL Configuration
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "Sxr_20050819"
    MYSQL_DB: str = "ITS"

    # Upload Configuration
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 1024000  # 1000KB default

    # JWT Configuration
    SECRET_KEY: str = "qA3v7x_zkDp9mR2gLbN8sWtYwF1jH5uKXeP0oIyV6lZnCf4"
    JWT_SECRET_KEY: str = "qA3v7x_zkDp9mR2gLbN8sWtYwF1jH5uKXeP0oIyV6lZnCf4"
    ALGORITHM: str = "HS256"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # RAG System Configuration
    VECTOR_CACHE_DIR: str = "vector_cache"
    
    # API Keys
    DASHSCOPE_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""

    # Neo4j Configuration
    NEO4J_URI: str = "neo4j://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "11111111"
    
    # MongoDB Configuration
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "chat_history"

    # CORS Configuration
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings() 
