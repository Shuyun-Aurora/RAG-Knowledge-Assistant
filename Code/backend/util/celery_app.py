import os

# # 禁用 ChromaDB / LangChain telemetry
# os.environ["CHROMA_TELEMETRY"] = "FALSE"
# os.environ['FORKED_BY_MULTIPROCESSING'] = '1'
# os.environ['ANONYMIZED_TELEMETRY'] = 'False'

# # ---- monkey patch chromadb telemetry 避免 capture() 报错 ----
# try:
#     import chromadb.telemetry.posthog
#     chromadb.telemetry.posthog.capture = lambda *args, **kwargs: None
# except ImportError:
#     pass

# # ---- 如果你也使用了 langchain 或 llamaindex，可以加上 ----
# try:
#     import langchain_community.telemetry
#     langchain_community.telemetry.capture = lambda *args, **kwargs: None
# except ImportError:
#     pass

from celery import Celery

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

celery_app.conf.update(
    task_track_started=True,
    task_soft_time_limit=3600,  # 改为 soft limit
)

# 显式导入所有任务模块，确保它们被注册
import task.document_tasks # 写任务文件的实际python包路径
