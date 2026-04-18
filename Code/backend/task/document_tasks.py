# app/task/document_tasks.py
from billiard.exceptions import SoftTimeLimitExceeded

from util.celery_app import celery_app
from service.rag_service import rag_service  # 统一实例管理

@celery_app.task(bind=True, max_retries=3)
def process_one_file_task(
    self,
    file_content,
    filename,
    course_name,
    parse_method,
    file_id,
    generate_knowledge_graph
):
    """
    异步处理单个文件任务。
    - 自动重试（最多3次）
    - 捕获 mineru CLI 的 SystemExit(0)
    - 捕获 SoftTimeLimitExceeded 超时
    """
    try:
        rag_service.process_one_file_async(
            file_content, filename, course_name, parse_method, file_id, generate_knowledge_graph
        )

    except SoftTimeLimitExceeded:
        print(f"⚠️ 文件 {filename} 超过 soft limit（600 秒），任务已中止但不会报错。")

    except SystemExit as e:
        # mineru.cli.main() 内部会调用 sys.exit(0)
        # Celery Worker 遇到 SystemExit 会误以为 Worker crash
        # 因此这里要手动拦截并吞掉
        if e.code == 0:
            print(f"✅ mineru 正常退出 (SystemExit {e.code})，文件 {filename}")
        else:
            print(f"❌ mineru 异常退出 (SystemExit {e.code})，文件 {filename}")
            # 非正常退出时可选择重试
            raise self.retry(exc=RuntimeError(f"mineru exited with code {e.code}"), countdown=10)

    except Exception as e:
        # 其他异常统一重试
        print(f"❌ 处理文件 {filename} 时出现异常：{e}")
        raise self.retry(exc=e, countdown=10)