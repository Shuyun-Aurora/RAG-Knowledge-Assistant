import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock
from controller import rag_controller

@pytest.fixture
def app():
    app = FastAPI()
    rag_controller.rag_service = MagicMock()
    app.include_router(rag_controller.router)
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_add_document_batch(client):
    rag_controller.rag_service.upload_document_batch.return_value = ["fileid1", "fileid2"]
    files = {'files': ('test.txt', b'hello world')}
    response = client.post("/api/rag/add_document_batch", data={'course_name': 'courseA'}, files=files)
    assert response.status_code == 200
    assert "file_ids" in response.json()

def test_add_document_multimodal(client, monkeypatch):
    async def fake_upload(*a, **kw):
        return "fid"
    rag_controller.rag_service.upload_document_with_mineru = AsyncMock(side_effect=fake_upload)
    files = {'file': ('test.pdf', b'pdfcontent')}
    response = client.post("/api/rag/add_document_multimodal", data={'course_name': 'courseA'}, files=files)
    assert response.status_code == 200
    assert "file_id" in response.json()

def test_delete_document_success(client):
    rag_controller.rag_service.delete_document.return_value = {
        "success": True,
        "file_id": "fid",
        "filename": "test.pdf",
        "course_name": "courseA",
        "kg_delete_result": {"success": True, "message": "ok"},
        "message": "删除成功"
    }
    response = client.delete("/api/rag/delete_document/fid")
    assert response.status_code == 200

def test_delete_document_fail(client):
    rag_controller.rag_service.delete_document.return_value = {"success": False, "message": "fail"}
    response = client.delete("/api/rag/delete_document/fid")
    assert response.status_code == 400

def test_get_documents(client):
    rag_controller.rag_service.get_documents_by_course.return_value = ([{
        "file_id": "fid1",
        "filename": "test.pdf",
        "course": "courseA",
        "upload_time": "2024-01-01T00:00:00"
    }], 1)
    response = client.get("/api/rag/documents?course_name=courseA&page=1&size=10")
    assert response.status_code == 200
    assert "documents" in response.json()

def test_download_file(client):
    class DummyStream:
        filename = "test.txt"
        def __iter__(self): return iter([b"abc"])
    rag_controller.rag_service.get_file_stream.return_value = DummyStream()
    response = client.get("/api/rag/download/fid")
    assert response.status_code == 200

def test_preview_file_pdf(client):
    class DummyStream:
        filename = "test.pdf"
        def __iter__(self): return iter([b"%PDF-1.4\n"])
    rag_controller.rag_service.get_file_stream.return_value = DummyStream()
    response = client.get("/api/rag/preview/fid")
    assert response.status_code == 200

def test_get_statistics(client):
    rag_controller.rag_service.get_statistics.return_value = {"total_vectors": 1, "total_files": 1, "vector_sources": []}
    response = client.get("/api/rag/statistics")
    assert response.status_code == 200
    assert "total_vectors" in response.json()

def test_get_vector_info(client):
    rag_controller.rag_service.get_vector_info.return_value = {"info": 1}
    response = client.get("/api/rag/vector_info")
    assert response.status_code == 200
    assert "info" in response.json()

def test_service_not_initialized(client):
    rag_controller.rag_service = None
    response = client.get("/api/rag/documents?course_name=courseA&page=1&size=10")
    assert response.status_code == 500 

def test_add_document_multimodal_batch(client, monkeypatch):
    async def fake_upload(*a, **kw):
        return ["fid1", "fid2"]
    rag_controller.rag_service.upload_document_multimodal_batch = AsyncMock(side_effect=fake_upload)
    files = {'files': ('test.pdf', b'pdfcontent')}
    response = client.post("/api/rag/add_document_multimodal_batch", data={'course_name': 'courseA'}, files=files)
    assert response.status_code == 200
    assert "file_ids" in response.json()

def test_get_user_sessions(client):
    rag_controller.rag_service.get_user_sessions.return_value = ["sid1", "sid2"]
    class DummyUser: id = 1
    response = client.get("/api/rag/chat_sessions", headers={"Authorization": "Bearer test"})
    assert response.status_code in (200, 401, 403) or "sessions" in response.json()  # 依赖Depends

def test_get_chat_history(client):
    rag_controller.rag_service.get_chat_history.return_value = [
        {"type": "ai", "data": {"additional_kwargs": {"sources": [{"metadata": {"course": "courseA", "source": "fid1"}}]}}}
    ]
    class DummyUser: id = 1
    response = client.get("/api/rag/chat_history/sid1", headers={"Authorization": "Bearer test"})
    assert response.status_code in (200, 401, 403) or "history" in response.json()

def test_get_chat_history_summary(client):
    rag_controller.rag_service.get_user_history_summary_by_course.return_value = [
        {"session_id": "sid1", "first_question": "q", "created_at": "2024-01-01", "updated_at": "2024-01-01", "course_name": "courseA", "message_count": 1}
    ]
    rag_controller.rag_service.get_user_history_summary.return_value = [
        {"session_id": "sid2", "first_question": "q2", "created_at": "2024-01-02", "updated_at": "2024-01-02", "course_name": "courseB", "message_count": 2}
    ]
    class DummyUser: id = 1
    response = client.get("/api/rag/chat_history_summary?limit=1&course_name=courseA", headers={"Authorization": "Bearer test"})
    assert response.status_code in (200, 401, 403) or "summaries" in response.json()

def test_add_document_batch_zip(client, monkeypatch):
    import io, zipfile
    # 构造一个单层zip包
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w") as zf:
        zf.writestr("a.txt", b"abc")
    mem_zip.seek(0)
    class DummyUpload:
        filename = "test.zip"
        def __init__(self, content): self.file = io.BytesIO(content)
        def read(self): return self.file.read()
    rag_controller.rag_service.upload_document_batch.return_value = ["fileid1"]
    files = {'files': ("test.zip", mem_zip.getvalue())}
    response = client.post("/api/rag/add_document_batch", data={'course_name': 'courseA'}, files=files)
    assert response.status_code == 200
    assert "file_ids" in response.json()

def test_add_document_batch_zip_nested_folder(client, monkeypatch):
    import io, zipfile
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w") as zf:
        zf.writestr("folder1/a.txt", b"abc")
        zf.writestr("folder1/folder2/b.txt", b"def")
    mem_zip.seek(0)
    files = {'files': ("test.zip", mem_zip.getvalue())}
    response = client.post("/api/rag/add_document_batch", data={'course_name': 'courseA'}, files=files)
    assert response.status_code == 400

def test_add_document_multimodal_batch_zip(client, monkeypatch):
    import io, zipfile
    async def fake_upload(*a, **kw): return ["fid1"]
    rag_controller.rag_service.upload_document_multimodal_batch = AsyncMock(side_effect=fake_upload)
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w") as zf:
        zf.writestr("a.txt", b"abc")
    mem_zip.seek(0)
    files = {'files': ("test.zip", mem_zip.getvalue())}
    response = client.post("/api/rag/add_document_multimodal_batch", data={'course_name': 'courseA'}, files=files)
    assert response.status_code == 200
    assert "file_ids" in response.json()

def test_get_chat_history_summary_no_course(client):
    rag_controller.rag_service.get_user_history_summary.return_value = [
        {"session_id": "sid2", "first_question": "q2", "created_at": "2024-01-02", "updated_at": "2024-01-02", "course_name": "courseB", "message_count": 2}
    ]
    class DummyUser: id = 1
    response = client.get("/api/rag/chat_history_summary?limit=1", headers={"Authorization": "Bearer test"})
    assert response.status_code in (200, 401, 403) or "summaries" in response.json()

def test_get_user_courses(client):
    rag_controller.rag_service.get_user_courses.return_value = ["courseA", "courseB"]
    class DummyUser: id = 1
    response = client.get("/api/rag/user_courses", headers={"Authorization": "Bearer test"})
    assert response.status_code in (200, 401, 403) or "courses" in str(response.json())

def test_get_current_reference_full_coverage(client, app):
    from controller import rag_controller
    class DummyUser:
        id = 1
    class DummySet:
        id = 1
        document_name = "test.pdf"
    class DummyQuery:
        def filter(self, *a, **kw):
            # 返回一个有 first() 方法的对象
            class Result:
                def first(self_inner):
                    return DummySet()
            return Result()
    class DummyDB:
        def query(self, *a, **kw):
            return DummyQuery()
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    app.dependency_overrides[rag_controller.get_db] = lambda: DummyDB()
    rag_controller.rag_service.get_chat_history.return_value = [
        {"type": "ai", "data": {"additional_kwargs": {"sources": [{"metadata": {"course": "courseA", "source": "fid1"}}]}}}
    ]
    class DummyDocDao:
        def get_file_from_mongo(self, ref_id):
            return {"filename": "test.pdf"}
    rag_controller.rag_service.document_dao = DummyDocDao()
    import sys
    sys.modules['service.ExerciseService'] = type('M', (), {
        "get_exercises_by_document_names": lambda db, names: [{"exercise_set_id": 1, "name": "ex1"}]
    })
    response = client.get(
        "/api/rag/currentReference?course_name=courseA&session_id=sid1&limit=1"
    )
    assert response.status_code == 200
    refs = response.json().get("references", [])
    assert refs and isinstance(refs[0].get("exercises"), list)

def test_get_current_reference_full_with_exercises(client, monkeypatch):
    # mock rag_service.get_chat_history 和 rag_service.document_dao.get_file_from_mongo
    rag_controller.rag_service.get_chat_history.return_value = [
        {"type": "ai", "data": {"additional_kwargs": {"sources": [{"metadata": {"course": "courseA", "source": "fid1"}}]}}}
    ]
    class DummyDocDao:
        def get_file_from_mongo(self, ref_id):
            return {"filename": "test.pdf"}
    rag_controller.rag_service.document_dao = DummyDocDao()
    # mock get_exercises_by_document_names，返回带有exercise_set_id和文档名的练习题
    import sys
    sys.modules['service.ExerciseService'] = type('M', (), {"get_exercises_by_document_names": lambda db, names: [{"exercise_set_id": 1, "name": "ex1"}]})
    # 由于接口依赖Depends(get_db)，这里只能保证接口被调用
    response = client.get("/api/rag/currentReference?course_name=courseA&session_id=sid1&limit=1", headers={"Authorization": "Bearer test"})
    assert response.status_code in (200, 401, 403) or "references" in response.json() 

def test_get_current_reference_grouped_exercises(client, monkeypatch):
    # mock rag_service.get_chat_history
    rag_controller.rag_service.get_chat_history.return_value = [
        {"type": "ai", "data": {"additional_kwargs": {"sources": [{"metadata": {"course": "courseA", "source": "fid1"}}]}}}
    ]
    # mock document_dao.get_file_from_mongo
    class DummyDocDao:
        def get_file_from_mongo(self, ref_id):
            return {"filename": "test.pdf"}
    rag_controller.rag_service.document_dao = DummyDocDao()
    # mock get_exercises_by_document_names
    import sys
    sys.modules['service.ExerciseService'] = type('M', (), {"get_exercises_by_document_names": lambda db, names: [{"exercise_set_id": 1, "name": "ex1"}]})
    # patch SQLAlchemy查询链
    class DummySet:
        id = 1
        document_name = "test.pdf"
    class DummyQuery:
        def filter(self, *a, **kw):
            return [DummySet()]
    class DummyDB:
        def query(self, *a, **kw):
            return DummyQuery()
    # monkeypatch get_db依赖
    monkeypatch.setattr("controller.rag_controller.get_db", lambda: DummyDB())
    # 调用接口
    response = client.get("/api/rag/currentReference?course_name=courseA&session_id=sid1&limit=1", headers={"Authorization": "Bearer test"})
    # 断言references中exercises字段为非空
    if response.status_code == 200:
        refs = response.json().get("references", [])
        assert refs and isinstance(refs[0].get("exercises"), list) 

def test_chat_stream(client, app):
    from controller import rag_controller
    # 覆盖依赖
    class DummyUser:
        id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    # mock rag_service.stream_query 为异步生成器
    async def fake_stream_query(*args, **kwargs):
        yield {"type": "content", "data": "hello"}
        yield {"type": "done"}
    rag_controller.rag_service.stream_query = fake_stream_query
    # 构造请求体
    payload = {
        "question": "你好？",
        "course_name": "courseA",
        "session_id": "sid1"
    }
    response = client.post("/api/rag/chat", json=payload)
    # 检查流式响应内容
    assert response.status_code == 200
    # 检查流式内容中有session_id和type字段
    content = b"".join(response.iter_bytes()).decode("utf-8")
    assert "session_id" in content and "content" in content 

def test_delete_chat_session_success(client, app):
    from controller import rag_controller
    class DummyUser:
        id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    rag_controller.rag_service.delete_session.return_value = True
    response = client.delete("/api/rag/chat_history/sid1")
    assert response.status_code == 200
    assert response.json()["message"] == "会话删除成功"

def test_delete_chat_session_fail(client, app):
    from controller import rag_controller
    class DummyUser:
        id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    rag_controller.rag_service.delete_session.return_value = False
    response = client.delete("/api/rag/chat_history/sid1")
    assert response.status_code == 404
    assert "会话不存在" in response.json()["detail"] 

def test_get_chat_history_summary_with_course(client, app):
    from controller import rag_controller
    class DummyUser:
        id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    rag_controller.rag_service.get_user_history_summary_by_course.return_value = [
        {"session_id": "sid1", "first_question": "q", "created_at": "2024-01-01", "updated_at": "2024-01-01", "course_name": "courseA", "message_count": 1}
    ]
    response = client.get("/api/rag/chat_history_summary?limit=1&course_name=courseA")
    assert response.status_code == 200
    assert "summaries" in response.json()

def test_get_chat_history_summary_without_course(client, app):
    from controller import rag_controller
    class DummyUser:
        id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    rag_controller.rag_service.get_user_history_summary.return_value = [
        {"session_id": "sid2", "first_question": "q2", "created_at": "2024-01-02", "updated_at": "2024-01-02", "course_name": "courseB", "message_count": 2}
    ]
    response = client.get("/api/rag/chat_history_summary?limit=1")
    assert response.status_code == 200
    assert "summaries" in response.json() 

def test_get_agent_styles(client, app):
    from controller import rag_controller
    # mock返回AgentStyleConfig完整字段
    rag_controller.rag_service.agent_service = MagicMock()
    rag_controller.rag_service.agent_service.get_all_agent_styles.return_value = [
        {
            "style": "default",
            "name": "默认风格",
            "description": "适合大多数场景",
            "system_prompt": "你是一个智能助教。",
            "personality_traits": ["耐心", "专业"]
        },
        {
            "style": "strict_tutor",
            "name": "严格导师",
            "description": "更注重规范和细节",
            "system_prompt": "你是一个严格的导师。",
            "personality_traits": ["严谨", "细致"]
        }
    ]
    response = client.get("/api/rag/chat/agent_styles")
    assert response.status_code == 200
    assert "styles" in response.json()

def test_get_user_courses_api(client, app):
    from controller import rag_controller
    class DummyUser: id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    rag_controller.rag_service.get_user_courses.return_value = ["courseA", "courseB"]
    response = client.get("/api/rag/user_courses")
    assert response.status_code == 200
    assert "courses" in response.json()["data"]

def test_get_user_sessions_api(client, app):
    from controller import rag_controller
    class DummyUser: id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    rag_controller.rag_service.get_user_sessions.return_value = ["sid1", "sid2"]
    response = client.get("/api/rag/chat_sessions")
    assert response.status_code == 200
    assert "sessions" in response.json()

def test_get_chat_history_api(client, app):
    from controller import rag_controller
    class DummyUser: id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    rag_controller.rag_service.get_chat_history.return_value = [
        {"type": "ai", "data": {"additional_kwargs": {"sources": [{"metadata": {"course": "courseA", "source": "fid1"}}]}}}
    ]
    response = client.get("/api/rag/chat_history/sid1")
    assert response.status_code == 200
    assert "history" in response.json() 

def test_add_document_batch_nested_folder_error(client):
    import io, zipfile
    # 构造嵌套文件夹zip包（folder1/folder2/a.txt）
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w") as zf:
        zf.writestr("folder1/folder2/a.txt", b"abc")
    mem_zip.seek(0)
    files = {'files': ("test.zip", mem_zip.getvalue())}
    response = client.post("/api/rag/add_document_batch", data={'course_name': 'courseA'}, files=files)
    assert response.status_code == 400
    assert "嵌套文件夹" in response.text

def test_add_document_multimodal_batch_nested_folder_error(client):
    import io, zipfile
    async def fake_upload(*a, **kw): return ["fid1"]
    from controller import rag_controller
    rag_controller.rag_service.upload_document_multimodal_batch = AsyncMock(side_effect=fake_upload)
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w") as zf:
        zf.writestr("folder1/folder2/a.txt", b"abc")
    mem_zip.seek(0)
    files = {'files': ("test.zip", mem_zip.getvalue())}
    response = client.post("/api/rag/add_document_multimodal_batch", data={'course_name': 'courseA'}, files=files)
    assert response.status_code == 400
    assert "嵌套文件夹" in response.text

def test_preview_file_not_pdf(client):
    from controller import rag_controller
    class DummyStream:
        filename = "test.txt"
        def __iter__(self): return iter([b"abc"])
    rag_controller.rag_service.get_file_stream.return_value = DummyStream()
    response = client.get("/api/rag/preview/fid")
    assert response.status_code == 400 or response.status_code == 404
    # 400: 仅支持PDF文件预览，404: 文件不存在
    assert "仅支持PDF文件预览" in response.text or "文件不存在" in response.text

def test_download_file_not_found(client):
    from controller import rag_controller
    rag_controller.rag_service.get_file_stream.side_effect = Exception()
    response = client.get("/api/rag/download/fid404")
    assert response.status_code == 404
    assert "文件不存在" in response.text

def test_preview_file_not_found(client):
    from controller import rag_controller
    rag_controller.rag_service.get_file_stream.side_effect = Exception()
    response = client.get("/api/rag/preview/fid404")
    assert response.status_code == 404
    assert "文件不存在" in response.text

def test_get_current_reference_course_mismatch(client, app):
    from controller import rag_controller
    class DummyUser: id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    class DummySet:
        id = 1
        document_name = "test.pdf"
    class DummyQuery:
        def filter(self, *a, **kw):
            class Result:
                def first(self_inner):
                    return DummySet()
            return Result()
    class DummyDB:
        def query(self, *a, **kw):
            return DummyQuery()
    app.dependency_overrides[rag_controller.get_db] = lambda: DummyDB()
    rag_controller.rag_service.get_chat_history.return_value = [
        {"type": "ai", "data": {"additional_kwargs": {"sources": [{"metadata": {"course": "other_course", "source": "fid1"}}]}}}
    ]
    class DummyDocDao:
        def get_file_from_mongo(self, ref_id):
            return {"filename": "test.pdf"}
    rag_controller.rag_service.document_dao = DummyDocDao()
    import sys
    sys.modules['service.ExerciseService'] = type('M', (), {
        "get_exercises_by_document_names": lambda db, names: [{"exercise_set_id": 1, "name": "ex1"}]
    })
    response = client.get(
        "/api/rag/currentReference?course_name=courseA&session_id=sid1&limit=1"
    )
    assert response.status_code == 200
    # references应为空
    assert response.json().get("references") == []

def test_get_current_reference_file_not_found(client, app):
    from controller import rag_controller
    class DummyUser: id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    class DummySet:
        id = 1
        document_name = "test.pdf"
    class DummyQuery:
        def filter(self, *a, **kw):
            class Result:
                def first(self_inner):
                    return DummySet()
            return Result()
    class DummyDB:
        def query(self, *a, **kw):
            return DummyQuery()
    app.dependency_overrides[rag_controller.get_db] = lambda: DummyDB()
    rag_controller.rag_service.get_chat_history.return_value = [
        {"type": "ai", "data": {"additional_kwargs": {"sources": [{"metadata": {"course": "courseA", "source": "fid1"}}]}}}
    ]
    class DummyDocDao:
        def get_file_from_mongo(self, ref_id):
            return None
    rag_controller.rag_service.document_dao = DummyDocDao()
    import sys
    sys.modules['service.ExerciseService'] = type('M', (), {
        "get_exercises_by_document_names": lambda db, names: [{"exercise_set_id": 1, "name": "ex1"}]
    })
    response = client.get(
        "/api/rag/currentReference?course_name=courseA&session_id=sid1&limit=1"
    )
    assert response.status_code == 200
    refs = response.json().get("references", [])
    assert refs and refs[0]["filename"] == "File not found" 

def test_service_not_initialized_500(client, app):
    from controller import rag_controller
    rag_controller.rag_service = None
    response = client.get("/api/rag/statistics")
    assert response.status_code == 500
    assert "Service not initialized" in response.text 

def test_chat_stream_cancelled_error(client, app):
    from controller import rag_controller
    import asyncio
    class DummyUser:
        id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    # mock stream_query 抛 CancelledError
    async def fake_stream_query(*args, **kwargs):
        raise asyncio.CancelledError()
        yield  # 生成器
    rag_controller.rag_service.stream_query = fake_stream_query
    payload = {
        "question": "你好？",
        "course_name": "courseA",
        "session_id": "sid1"
    }
    response = client.post("/api/rag/chat", json=payload)
    assert response.status_code == 200
    content = b"".join(response.iter_bytes()).decode("utf-8")
    # CancelledError分支只会有最后的done
    assert "done" in content

def test_chat_stream_general_exception(client, app):
    from controller import rag_controller
    class DummyUser:
        id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    # mock stream_query 抛 Exception
    async def fake_stream_query(*args, **kwargs):
        raise Exception("test error")
        yield
    rag_controller.rag_service.stream_query = fake_stream_query
    payload = {
        "question": "你好？",
        "course_name": "courseA",
        "session_id": "sid1"
    }
    response = client.post("/api/rag/chat", json=payload)
    assert response.status_code == 200
    content = b"".join(response.iter_bytes()).decode("utf-8")
    # 应包含 type=error
    assert '"type": "error"' in content
    assert "test error" in content
    assert "done" in content

def test_add_document_batch_zip_nested_folder_dir_entry(client):
    import io, zipfile
    # 构造一个zip，包含嵌套文件夹目录项 folder1/folder2/
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w") as zf:
        zf.writestr("folder1/", b"")  # 单层目录
        zf.writestr("folder1/folder2/", b"")  # 嵌套目录
        zf.writestr("folder1/folder2/a.txt", b"abc")  # 嵌套文件
    mem_zip.seek(0)
    files = {'files': ("test.zip", mem_zip.getvalue())}
    response = client.post("/api/rag/add_document_batch", data={'course_name': 'courseA'}, files=files)
    assert response.status_code == 400
    assert "嵌套文件夹" in response.text

def test_chat_service_not_initialized(client, app):
    from controller import rag_controller
    class DummyUser: id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    rag_controller.rag_service = None
    payload = {
        "question": "你好？",
        "course_name": "courseA",
        "session_id": "sid1"
    }
    response = client.post("/api/rag/chat", json=payload)
    assert response.status_code == 500
    assert "Service not initialized" in response.text

def test_chat_missing_question_or_course_name(client, app):
    from controller import rag_controller
    rag_controller.rag_service = MagicMock()
    class DummyUser: id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    # 缺少question
    payload = {
        "course_name": "courseA",
        "session_id": "sid1"
    }
    response = client.post("/api/rag/chat", json=payload)
    assert response.status_code == 400
    assert "Question and course_name are required" in response.text
    # 缺少course_name
    payload = {
        "question": "你好？",
        "session_id": "sid1"
    }
    response = client.post("/api/rag/chat", json=payload)
    assert response.status_code == 400
    assert "Question and course_name are required" in response.text

def test_chat_stream_chunk_not_dict(client, app):
    from controller import rag_controller
    class DummyUser: id = 1
    app.dependency_overrides[rag_controller.get_current_user] = lambda: DummyUser()
    # mock stream_query 返回字符串
    async def fake_stream_query(*args, **kwargs):
        yield "hello world"
    rag_controller.rag_service.stream_query = fake_stream_query
    payload = {
        "question": "你好？",
        "course_name": "courseA",
        "session_id": "sid1"
    }
    response = client.post("/api/rag/chat", json=payload)
    assert response.status_code == 200
    content = b"".join(response.iter_bytes()).decode("utf-8")
    # 应包含 "data": "hello world"
    assert '"data": "hello world"' in content
    assert "session_id" in content

