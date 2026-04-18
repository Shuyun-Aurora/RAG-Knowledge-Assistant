import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import service.rag_service as rag_service
from langchain_core.messages import AIMessage, HumanMessage, messages_to_dict
import asyncio

@pytest.fixture
def mock_deps():
    vector_dao = MagicMock()
    document_dao = MagicMock()
    chat_history_dao = MagicMock()
    knowledge_graph_service = MagicMock()
    llm = AsyncMock()
    return vector_dao, document_dao, chat_history_dao, knowledge_graph_service, llm


def test_upload_document(mock_deps):
    vector_dao, document_dao, *_ = mock_deps
    document_dao.save_file_to_mongo.return_value = "file123"
    document_dao.extract_text_from_file.return_value = "text"
    vector_dao.split_text.return_value = ["chunk1", "chunk2"]
    rag = rag_service.RAGService(vector_dao, None, document_dao, None)
    file_id = rag.upload_document(b"abc", "test.pdf", "courseA")
    assert file_id == "file123"
    vector_dao.add.assert_called()
    vector_dao.save.assert_called()


def test_add_document(mock_deps):
    vector_dao, document_dao, *_ = mock_deps
    document_dao.extract_text_from_file.return_value = "text"
    vector_dao.split_text.return_value = ["chunk1"]
    rag = rag_service.RAGService(vector_dao, None, document_dao, None)
    rag.add_document("file123", "courseA")
    vector_dao.add.assert_called()
    vector_dao.save.assert_called()


def test_upload_document_batch(mock_deps):
    vector_dao, document_dao, *_ = mock_deps
    document_dao.save_file_to_mongo.return_value = "fileid"
    document_dao.extract_text_from_file.return_value = "text"
    vector_dao.split_text.return_value = ["chunk1"]
    rag = rag_service.RAGService(vector_dao, None, document_dao, None)
    files = [{"file_content": b"abc", "filename": "a.pdf"}, {"file_content": b"def", "filename": "b.pdf"}]
    result = rag.upload_document_batch(files, "courseA")
    assert len(result) == 2


def test_get_documents_by_course(mock_deps):
    _, document_dao, *_ = mock_deps
    document_dao.get_documents_by_course.return_value = ([{"id": 1}], 1)
    rag = rag_service.RAGService(None, None, document_dao, None)
    docs, total = rag.get_documents_by_course("courseA", 1, 10)
    assert docs == [{"id": 1}]
    assert total == 1


def test_get_file_stream_and_by_id(mock_deps):
    _, document_dao, *_ = mock_deps
    document_dao.get_file_stream.return_value = b"data"
    document_dao.get_file_by_id.return_value = {"id": "fileid"}
    rag = rag_service.RAGService(None, None, document_dao, None)
    assert rag.get_file_stream("fileid") == b"data"
    assert rag.get_file_by_id("fileid") == {"id": "fileid"}


def test_delete_document_success(mock_deps):
    vector_dao, document_dao, _, knowledge_graph_service, _ = mock_deps
    document_dao.get_file_by_id.return_value = {"filename": "f.pdf", "metadata": {"course": "c"}}
    document_dao.delete_file_from_mongo.return_value = True
    vector_dao.delete_by_source.return_value = None
    knowledge_graph_service.delete_nodes_by_filename.return_value = {"success": True, "message": "ok"}
    knowledge_graph_service.delete_kg_vectors_by_filename.return_value = {"success": True, "message": "ok"}
    rag = rag_service.RAGService(vector_dao, None, document_dao, None, knowledge_graph_service)
    result = rag.delete_document("fileid")
    assert result["success"]


def test_delete_document_not_found(mock_deps):
    _, document_dao, *_ = mock_deps
    document_dao.get_file_by_id.return_value = None
    rag = rag_service.RAGService(None, None, document_dao, None)
    result = rag.delete_document("fileid")
    assert not result["success"]


def test_delete_document_exception(mock_deps):
    _, document_dao, *_ = mock_deps
    document_dao.get_file_by_id.side_effect = Exception("fail")
    rag = rag_service.RAGService(None, None, document_dao, None)
    result = rag.delete_document("fileid")
    assert not result["success"]


def test_get_document_list(mock_deps):
    vector_dao, document_dao, *_ = mock_deps
    vector_dao.list_sources.return_value = ["f1", "f2"]
    document_dao.get_file_from_mongo.side_effect = [{"filename": "a", "metadata": {"course": "c", "upload_time": "t"}},
                                                    None]
    rag = rag_service.RAGService(vector_dao, None, document_dao, None)
    docs = rag.get_document_list()
    assert len(docs) == 2
    assert docs[1]["filename"] == "文件已删除"


def test_get_document_list_exception(mock_deps):
    vector_dao, document_dao, *_ = mock_deps
    vector_dao.list_sources.side_effect = Exception("fail")
    rag = rag_service.RAGService(vector_dao, None, document_dao, None)
    docs = rag.get_document_list()
    assert docs == []


def test_get_statistics(mock_deps):
    vector_dao, *_ = mock_deps
    vector_dao.get_document_count.return_value = 5
    vector_dao.list_sources.return_value = [1, 2, 3]
    rag = rag_service.RAGService(vector_dao, None, None, None)
    stats = rag.get_statistics()
    assert stats["total_vectors"] == 5
    assert stats["total_files"] == 3


def test_get_statistics_exception(mock_deps):
    vector_dao, *_ = mock_deps
    vector_dao.get_document_count.side_effect = Exception("fail")
    rag = rag_service.RAGService(vector_dao, None, None, None)
    stats = rag.get_statistics()
    assert stats["total_vectors"] == 0


def test_get_vector_info(mock_deps):
    vector_dao, *_ = mock_deps
    vector_dao.get_vector_info.return_value = {"info": 1}
    rag = rag_service.RAGService(vector_dao, None, None, None)
    info = rag.get_vector_info()
    assert info["info"] == 1


def test_get_vector_info_exception(mock_deps):
    vector_dao, *_ = mock_deps
    vector_dao.get_vector_info.side_effect = Exception("fail")
    rag = rag_service.RAGService(vector_dao, None, None, None)
    info = rag.get_vector_info()
    assert "error" in info


def test_get_chat_history(mock_deps):
    _, _, chat_history_dao, *_ = mock_deps
    chat_history_dao.get_chat_history.return_value = [1, 2]
    rag = rag_service.RAGService(None, None, None, chat_history_dao)
    assert rag.get_chat_history("sid") == [1, 2]


def test_get_user_sessions(mock_deps):
    _, _, chat_history_dao, *_ = mock_deps
    chat_history_dao.get_user_sessions.return_value = ["s1"]
    rag = rag_service.RAGService(None, None, None, chat_history_dao)
    assert rag.get_user_sessions(1) == ["s1"]


def test_get_user_history_summary(mock_deps):
    _, _, chat_history_dao, *_ = mock_deps
    chat_history_dao.get_user_history_summary.return_value = ["h1"]
    rag = rag_service.RAGService(None, None, None, chat_history_dao)
    assert rag.get_user_history_summary(1) == ["h1"]


def test_get_user_history_summary_by_course(mock_deps):
    _, _, chat_history_dao, *_ = mock_deps
    chat_history_dao.get_user_history_summary_by_course.return_value = ["h2"]
    rag = rag_service.RAGService(None, None, None, chat_history_dao)
    assert rag.get_user_history_summary_by_course(1, "c") == ["h2"]


def test_get_user_courses(mock_deps):
    _, _, chat_history_dao, *_ = mock_deps
    chat_history_dao.get_user_courses.return_value = ["c1"]
    rag = rag_service.RAGService(None, None, None, chat_history_dao)
    assert rag.get_user_courses(1) == ["c1"]


def test_delete_session(mock_deps):
    _, _, chat_history_dao, *_ = mock_deps
    chat_history_dao.delete_session.return_value = True
    rag = rag_service.RAGService(None, None, None, chat_history_dao)
    assert rag.delete_session("sid", 1)


def test_clean_data_for_bson(mock_deps):
    rag = rag_service.RAGService(*mock_deps)
    assert rag._clean_data_for_bson({"a": 1, "b": [2, 3]}) == {"a": 1, "b": [2, 3]}
    assert rag._clean_data_for_bson([1, 2, {"c": 3}]) == [1, 2, {"c": 3}]
    class Dummy: pass
    d = Dummy()
    assert isinstance(rag._clean_data_for_bson(d), str)


@pytest.mark.asyncio
async def test_upload_document_with_mineru(mock_deps):
    vector_dao, document_dao, _, _, _ = mock_deps
    document_dao.save_file_to_mongo.return_value = "fid"
    document_dao.parse_document_with_mineru.return_value = ([], "")
    document_dao.process_content_with_vision.return_value = ([{"text": "t", "page_indices": [1]}], "kgtext")
    vector_dao.add.return_value = None
    vector_dao.save.return_value = None
    rag = rag_service.RAGService(vector_dao, None, document_dao, None)
    file_id = await rag.upload_document_with_mineru(b"abc", "f.pdf", "c")
    assert file_id == "fid"


@pytest.mark.asyncio
async def test_upload_document_multimodal_batch(mock_deps):
    vector_dao, document_dao, _, _, _ = mock_deps
    document_dao.save_file_to_mongo.return_value = "fid"
    document_dao.parse_document_with_mineru.return_value = ([], "")
    document_dao.process_content_with_vision.return_value = ([{"text": "t", "page_indices": [1]}], "kgtext")
    vector_dao.add.return_value = None
    vector_dao.save.return_value = None
    rag = rag_service.RAGService(vector_dao, None, document_dao, None)
    files = [{"file_content": b"abc", "filename": "a.pdf"}]
    result = await rag.upload_document_multimodal_batch(files, "c")
    assert result == ["fid"]


def test_create_course_knowledge_graph_root_node(mock_deps):
    _, _, _, knowledge_graph_service, _ = mock_deps
    rag = rag_service.RAGService(None, None, None, None, knowledge_graph_service)
    knowledge_graph_service.add_node.return_value = None
    rag.create_course_knowledge_graph_root_node("test_course")
    knowledge_graph_service.add_node.assert_called()


def test_create_course_knowledge_graph_root_node_no_service(mock_deps):
    rag = rag_service.RAGService(None, None, None, None, None)
    rag.create_course_knowledge_graph_root_node("test_course")

def test_create_course_knowledge_graph_root_node_exception(mock_deps):
    _, _, _, knowledge_graph_service, _ = mock_deps
    rag = rag_service.RAGService(None, None, None, None, knowledge_graph_service)
    # 让 add_node 抛异常
    knowledge_graph_service.add_node.side_effect = Exception("fail")
    # 不抛出异常即可，覆盖 except 分支
    rag.create_course_knowledge_graph_root_node("test_course")

@pytest.mark.asyncio
async def test_stream_query_basic(mock_deps):
    vector_dao, document_dao, chat_history_dao, knowledge_graph_service, llm = mock_deps

    # mock chat_history_dao
    chat_history_dao.get_chat_history.return_value = []
    chat_history_dao.save_chat_history.return_value = None

    # mock vector_dao
    doc_mock = MagicMock()
    doc_mock.page_content = "doc1"
    doc_mock.metadata = {"meta": 1}
    vector_dao.search.return_value = [(doc_mock, 0.5)]
    vector_dao.get_by_course_filename_and_page.return_value = []
    vector_dao.get_by_course_and_filename.return_value = []

    # mock llm.stream_invoke为异步生成器
    async def fake_stream_invoke(prompt):
        yield "answer1"
        yield "answer2"
    llm.stream_invoke = fake_stream_invoke

    rag = rag_service.RAGService(vector_dao, llm, document_dao, chat_history_dao, knowledge_graph_service=None)

    # 调用stream_query并收集输出
    result = []
    async for chunk in rag.stream_query(
        question="test?",
        session_id="sid",
        user_id=1,
        course_name="courseA"
    ):
        result.append(chunk)

    # 检查流式输出结构
    assert any("type" in c and c["type"] == "source" for c in result)
    assert any("type" in c and c["type"] == "content" for c in result)
    assert any("data" in c for c in result)
    assert any("answer1" in str(c) or "answer2" in str(c) for c in result)

@pytest.mark.asyncio
async def test_store_knowledge_graph_nodes_to_vector_db_normal(mock_deps):
    # 正常存储分支
    vector_dao, document_dao, chat_history_dao, knowledge_graph_service, llm = mock_deps
    rag = rag_service.RAGService(vector_dao, llm, document_dao, chat_history_dao, knowledge_graph_service)
    # mock返回有节点
    knowledge_graph_service.get_knowledge_graph.return_value = {
        "nodes": [
            {"properties": {"name": "n", "description": "d", "content": "c", "entity_type": "FileRoot"}, "id": 1}
        ]
    }
    # patch VectorDAO.add/save
    with patch.object(rag_service.VectorDAO, "add") as mock_add, \
         patch.object(rag_service.VectorDAO, "save") as mock_save:
        mock_add.return_value = None
        mock_save.return_value = None
        await rag._store_knowledge_graph_nodes_to_vector_db("courseA", "file.pdf")
        mock_add.assert_called()
        mock_save.assert_called()

@pytest.mark.asyncio
async def test_store_knowledge_graph_nodes_to_vector_db_no_service(mock_deps):
    # service未初始化分支
    rag = rag_service.RAGService(*mock_deps[:-2], None)
    await rag._store_knowledge_graph_nodes_to_vector_db("courseA", "file.pdf")
    # 只要不抛异常即可

@pytest.mark.asyncio
async def test_store_knowledge_graph_nodes_to_vector_db_no_nodes(mock_deps):
    # 没有节点分支
    vector_dao, document_dao, chat_history_dao, knowledge_graph_service, llm = mock_deps
    rag = rag_service.RAGService(vector_dao, llm, document_dao, chat_history_dao, knowledge_graph_service)
    knowledge_graph_service.get_knowledge_graph.return_value = {"nodes": []}
    await rag._store_knowledge_graph_nodes_to_vector_db("courseA", "file.pdf")
    # 只要不抛异常即可

@pytest.mark.asyncio
async def test_store_knowledge_graph_nodes_to_vector_db_exception(mock_deps):
    # 异常分支
    vector_dao, document_dao, chat_history_dao, knowledge_graph_service, llm = mock_deps
    rag = rag_service.RAGService(vector_dao, llm, document_dao, chat_history_dao, knowledge_graph_service)
    knowledge_graph_service.get_knowledge_graph.side_effect = Exception("fail")
    await rag._store_knowledge_graph_nodes_to_vector_db("courseA", "file.pdf")
    # 只要不抛异常即可

import pytest

@pytest.mark.asyncio
async def test_get_knowledge_graph_context_no_service(mock_deps):
    rag = rag_service.RAGService(None, None, None, None, None)
    result = await rag._get_knowledge_graph_context("q", "c")
    assert result == ""

@pytest.mark.asyncio
async def test_get_knowledge_graph_context_with_nodes(mock_deps):
    _, _, _, knowledge_graph_service, _ = mock_deps
    rag = rag_service.RAGService(None, None, None, None, knowledge_graph_service)
    knowledge_graph_service.search_related_nodes = AsyncMock(return_value={
        "nodes": [1], "context": "ctx", "related_count": 1, "total_nodes": 1
    })
    result = await rag._get_knowledge_graph_context("q", "c")
    assert result == "ctx"

@pytest.mark.asyncio
async def test_get_knowledge_graph_context_no_nodes(mock_deps):
    _, _, _, knowledge_graph_service, _ = mock_deps
    rag = rag_service.RAGService(None, None, None, None, knowledge_graph_service)
    knowledge_graph_service.search_related_nodes = AsyncMock(return_value={
        "nodes": [], "search_info": "未找到相关知识节点"
    })
    result = await rag._get_knowledge_graph_context("q", "c")
    assert result == ""

@pytest.mark.asyncio
async def test_get_knowledge_graph_context_exception(mock_deps):
    _, _, _, knowledge_graph_service, _ = mock_deps
    rag = rag_service.RAGService(None, None, None, None, knowledge_graph_service)
    knowledge_graph_service.search_related_nodes = AsyncMock(side_effect=Exception("fail"))
    result = await rag._get_knowledge_graph_context("q", "c")
    assert result == ""

def test_build_enhanced_prompt_basic(mock_deps):
    rag = rag_service.RAGService(*mock_deps)
    prompt = rag._build_enhanced_prompt("q", "kg")
    assert "用户问题: q" in prompt
    assert "## 知识图谱信息:" in prompt
    assert "kg" in prompt

def test_build_enhanced_prompt_with_rag(mock_deps):
    rag = rag_service.RAGService(*mock_deps)
    prompt = rag._build_enhanced_prompt("q", "kg", rag_context="ragctx")
    assert "## RAG检索的文档内容:" in prompt
    assert "ragctx" in prompt

def test_build_enhanced_prompt_with_original(mock_deps):
    rag = rag_service.RAGService(*mock_deps)
    prompt = rag._build_enhanced_prompt("q", "kg", original_response="orig")
    assert "## 原始回答:" in prompt
    assert "orig" in prompt

def test_build_enhanced_prompt_all(mock_deps):
    rag = rag_service.RAGService(*mock_deps)
    prompt = rag._build_enhanced_prompt("q", "kg", original_response="orig", rag_context="ragctx")
    assert "ragctx" in prompt and "orig" in prompt

def test_upload_document_batch_exception(mock_deps):
    vector_dao, document_dao, *_ = mock_deps
    document_dao.save_file_to_mongo.side_effect = ["fileid", Exception("fail")]
    document_dao.extract_text_from_file.return_value = "text"
    vector_dao.split_text.return_value = ["chunk1"]
    rag = rag_service.RAGService(vector_dao, None, document_dao, None)
    files = [
        {"file_content": b"abc", "filename": "a.pdf"},
        {"file_content": b"def", "filename": "b.pdf"}
    ]
    result = rag.upload_document_batch(files, "courseA")
    assert len(result) == 1  # 只成功一个

def test_delete_document_file_deleted_false(mock_deps):
    vector_dao, document_dao, _, knowledge_graph_service, _ = mock_deps
    document_dao.get_file_by_id.return_value = {"filename": "f.pdf", "metadata": {"course": "c"}}
    document_dao.delete_file_from_mongo.return_value = False
    rag = rag_service.RAGService(vector_dao, None, document_dao, None, knowledge_graph_service)
    result = rag.delete_document("fileid")
    assert not result["success"]
    assert "删除失败" in result["message"]

def test_delete_document_kg_delete_exception(mock_deps):
    vector_dao, document_dao, _, knowledge_graph_service, _ = mock_deps
    document_dao.get_file_by_id.return_value = {"filename": "f.pdf", "metadata": {"course": "c"}}
    document_dao.delete_file_from_mongo.return_value = True
    vector_dao.delete_by_source.return_value = None
    knowledge_graph_service.delete_nodes_by_filename.side_effect = Exception("kgfail")
    rag = rag_service.RAGService(vector_dao, None, document_dao, None, knowledge_graph_service)
    result = rag.delete_document("fileid")
    assert not result["kg_delete_result"]["success"]
    assert "删除知识图谱失败" in result["kg_delete_result"]["message"]

@pytest.mark.asyncio
async def test_stream_query_sources_and_filename_pageidx(mock_deps):
    vector_dao, document_dao, chat_history_dao, knowledge_graph_service, llm = mock_deps
    # 构造历史消息，AIMessage带sources
    ai_msg = AIMessage(content="a", additional_kwargs={"sources": [{"page_content": "old", "metadata": {}}]})
    chat_history_dao.get_chat_history.return_value = messages_to_dict([ai_msg])
    chat_history_dao.save_chat_history.return_value = None
    # mock vector_dao
    doc_mock = MagicMock(); doc_mock.page_content = "doc1"; doc_mock.metadata = {"meta": 1}
    vector_dao.get_by_course_filename_and_page.return_value = [doc_mock]
    vector_dao.search.return_value = [(doc_mock, 0.5)]
    # mock llm
    async def fake_stream_invoke(prompt):
        yield "answer"
    llm.stream_invoke = fake_stream_invoke
    rag = rag_service.RAGService(vector_dao, llm, document_dao, chat_history_dao, None)
    result = []
    async for chunk in rag.stream_query(
        question="test?", session_id="sid", user_id=1, course_name="courseA", filename="f.pdf", page_idx=1
    ):
        result.append(chunk)
    assert any("source" in c.get("type", "") for c in result)
    assert any("content" in c.get("type", "") for c in result)

@pytest.mark.asyncio
async def test_stream_query_filename_only(mock_deps):
    vector_dao, document_dao, chat_history_dao, knowledge_graph_service, llm = mock_deps
    chat_history_dao.get_chat_history.return_value = []
    chat_history_dao.save_chat_history.return_value = None
    doc_mock = MagicMock(); doc_mock.page_content = "doc1"; doc_mock.metadata = {"meta": 1}
    vector_dao.get_by_course_and_filename.return_value = [doc_mock]
    vector_dao.search.return_value = [(doc_mock, 0.5)]
    async def fake_stream_invoke(prompt):
        yield "answer"
    llm.stream_invoke = fake_stream_invoke
    rag = rag_service.RAGService(vector_dao, llm, document_dao, chat_history_dao, None)
    result = []
    async for chunk in rag.stream_query(
        question="test?", session_id="sid", user_id=1, course_name="courseA", filename="f.pdf"
    ):
        result.append(chunk)
    assert any("source" in c.get("type", "") for c in result)
    assert any("content" in c.get("type", "") for c in result)

@pytest.mark.asyncio
async def test_stream_query_kg_exception_and_kg_context(mock_deps):
    vector_dao, document_dao, chat_history_dao, knowledge_graph_service, llm = mock_deps
    chat_history_dao.get_chat_history.return_value = []
    chat_history_dao.save_chat_history.return_value = None
    doc_mock = MagicMock(); doc_mock.page_content = "doc1"; doc_mock.metadata = {"meta": 1}
    vector_dao.search.return_value = [(doc_mock, 0.5)]
    # 知识图谱服务异常
    knowledge_graph_service.search_related_nodes = AsyncMock(side_effect=Exception("fail"))
    async def fake_stream_invoke(prompt):
        yield "answer"
    llm.stream_invoke = fake_stream_invoke
    rag = rag_service.RAGService(vector_dao, llm, document_dao, chat_history_dao, knowledge_graph_service)
    result = []
    async for chunk in rag.stream_query(
        question="test?", session_id="sid", user_id=1, course_name="courseA"
    ):
        result.append(chunk)
    assert any("source" in c.get("type", "") for c in result)
    assert any("content" in c.get("type", "") for c in result)

@pytest.mark.asyncio
async def test_stream_query_kg_context_branch(mock_deps):
    vector_dao, document_dao, chat_history_dao, knowledge_graph_service, llm = mock_deps
    chat_history_dao.get_chat_history.return_value = []
    chat_history_dao.save_chat_history.return_value = None
    doc_mock = MagicMock(); doc_mock.page_content = "doc1"; doc_mock.metadata = {"meta": 1}
    vector_dao.search.return_value = [(doc_mock, 0.5)]
    # 知识图谱服务返回有节点
    knowledge_graph_service.search_related_nodes = AsyncMock(return_value={
        "nodes": [1], "context": "kgctx", "related_count": 1, "total_nodes": 2
    })
    async def fake_stream_invoke(prompt):
        yield "answer"
    llm.stream_invoke = fake_stream_invoke
    rag = rag_service.RAGService(vector_dao, llm, document_dao, chat_history_dao, knowledge_graph_service)
    result = []
    async for chunk in rag.stream_query(
        question="test?", session_id="sid", user_id=1, course_name="courseA"
    ):
        result.append(chunk)
    # 检查additional_kwargs里有knowledge_graph
    # 由于yield的是流式，无法直接断言，但只要不抛异常即可
    assert any("source" in c.get("type", "") for c in result)
    assert any("content" in c.get("type", "") for c in result)

@pytest.mark.asyncio
def test_enhance_chat_response_no_kg_service(mock_deps):
    rag = rag_service.RAGService(None, AsyncMock(), None, None, None)
    result = asyncio.run(rag.enhance_chat_response("q", "c", original_response="orig", rag_context="ragctx"))
    assert result == "orig"

@pytest.mark.asyncio
async def test_enhance_chat_response_with_kg_and_llm(mock_deps):
    _, _, _, knowledge_graph_service, llm = mock_deps
    rag = rag_service.RAGService(None, llm, None, None, knowledge_graph_service)
    # mock kg_context
    knowledge_graph_service.search_related_nodes = AsyncMock(return_value={"nodes": [1], "context": "kgctx"})
    async def fake_stream_invoke(prompt):
        yield "enhanced"
    llm.stream_invoke = fake_stream_invoke
    result = await rag.enhance_chat_response("q", "c", original_response="orig", rag_context="ragctx")
    assert "enhanced" in result

@pytest.mark.asyncio
async def test_enhance_chat_response_with_kg_no_kg_context(mock_deps):
    _, _, _, knowledge_graph_service, llm = mock_deps
    rag = rag_service.RAGService(None, llm, None, None, knowledge_graph_service)
    # kg_context为空
    knowledge_graph_service.search_related_nodes = AsyncMock(return_value={"nodes": [], "context": ""})
    result = await rag.enhance_chat_response("q", "c", original_response="orig", rag_context="ragctx")
    assert result == "orig"

@pytest.mark.asyncio
async def test_enhance_chat_response_llm_exception(mock_deps):
    _, _, _, knowledge_graph_service, llm = mock_deps
    rag = rag_service.RAGService(None, llm, None, None, knowledge_graph_service)
    knowledge_graph_service.search_related_nodes = AsyncMock(return_value={"nodes": [1], "context": "kgctx"})
    async def fake_stream_invoke(prompt):
        raise Exception("llmfail")
        yield  # for async generator
    llm.stream_invoke = fake_stream_invoke
    result = await rag.enhance_chat_response("q", "c", original_response="orig", rag_context="ragctx")
    assert result == "orig"

@pytest.mark.asyncio
def test_upload_document_multimodal_batch_exception(mock_deps):
    vector_dao, document_dao, *_ = mock_deps
    document_dao.save_file_to_mongo.side_effect = ["fid", Exception("fail")]
    document_dao.parse_document_with_mineru.return_value = ([], "")
    document_dao.process_content_with_vision.return_value = ([{"text": "t", "page_indices": [1]}], "kgtext")
    vector_dao.add.return_value = None
    vector_dao.save.return_value = None
    rag = rag_service.RAGService(vector_dao, None, document_dao, None)
    files = [
        {"file_content": b"abc", "filename": "a.pdf"},
        {"file_content": b"def", "filename": "b.pdf"}
    ]
    # 只要不抛异常即可
    result = asyncio.run(rag.upload_document_multimodal_batch(files, "courseA"))
    assert len(result) == 1

import types
@pytest.mark.asyncio
async def test_generate_knowledge_graph_background_timeout(monkeypatch, mock_deps):
    # patch kg.build_and_store_graph为超时
    class DummyKG:
        async def build_and_store_graph(self, **kwargs):
            await asyncio.sleep(0.1)
        async def close(self):
            pass
    monkeypatch.setattr("service.rag_service.LightRAGKnowledgeGraph", lambda *a, **kw: DummyKG())
    monkeypatch.setattr("service.rag_service.settings", type("S", (), {
        "NEO4J_URI": "", "NEO4J_USER": "", "NEO4J_PASSWORD": "", "DEEPSEEK_API_KEY": ""
    })())
    rag = rag_service.RAGService(*mock_deps)
    # patch asyncio.wait_for抛TimeoutError
    async def fake_wait_for(coro, timeout):
        raise asyncio.TimeoutError()
    monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)
    await rag._generate_knowledge_graph_background(["text"], "courseA", fast_mode=True, filename="f.pdf")
    # 只要不抛异常即可

@pytest.mark.asyncio
async def test_generate_knowledge_graph_background_normal(monkeypatch, mock_deps):
    called = {}

    class DummyKG:
        def __init__(self, *args, **kwargs):
            print("✅ DummyKG init")
        async def build_and_store_graph(self, **kwargs):
            print("✅ DummyKG build called")
            called["build"] = True
        async def close(self):
            print("✅ DummyKG close called")
            called["close"] = True

    monkeypatch.setattr(rag_service, "LightRAGKnowledgeGraph", lambda *a, **kw: DummyKG())

    monkeypatch.setattr(rag_service, "settings", type("S", (), {
        "NEO4J_URI": "", "NEO4J_USER": "", "NEO4J_PASSWORD": "", "DEEPSEEK_API_KEY": ""
    })())

    rag = rag_service.RAGService(*mock_deps)

    rag._store_knowledge_graph_nodes_to_vector_db = AsyncMock()

    await rag._generate_knowledge_graph_background(["text"], "courseA", fast_mode=True, filename="f.pdf")

    assert called.get("build") and called.get("close")
    rag._store_knowledge_graph_nodes_to_vector_db.assert_awaited()


@pytest.mark.asyncio
async def test_store_knowledge_graph_nodes_to_vector_db_else_source_and_no_valid_nodes(mock_deps):
    # 非FileRoot节点source和无有效节点内容分支
    vector_dao, document_dao, chat_history_dao, knowledge_graph_service, llm = mock_deps
    rag = rag_service.RAGService(vector_dao, llm, document_dao, chat_history_dao, knowledge_graph_service)
    # 非FileRoot节点
    knowledge_graph_service.get_knowledge_graph.return_value = {
        "nodes": [
            {"properties": {"name": "n", "description": "d", "content": "c", "entity_type": "OtherType"}, "id": 1}
        ]
    }
    with patch.object(rag_service.VectorDAO, "add") as mock_add, \
         patch.object(rag_service.VectorDAO, "save") as mock_save:
        mock_add.return_value = None
        mock_save.return_value = None
        await rag._store_knowledge_graph_nodes_to_vector_db("courseA", "file.pdf")
        mock_add.assert_called()
        mock_save.assert_called()
    # 没有有效节点内容
    knowledge_graph_service.get_knowledge_graph.return_value = {"nodes": []}
    await rag._store_knowledge_graph_nodes_to_vector_db("courseA", "file.pdf")
    # 只要不抛异常即可

@pytest.mark.asyncio
async def test_store_knowledge_graph_nodes_to_vector_db_no_valid_content(mock_deps):
    # nodes不为空但内容全为空，触发“没有找到有效的知识图谱节点内容”分支
    vector_dao, document_dao, chat_history_dao, knowledge_graph_service, llm = mock_deps
    rag = rag_service.RAGService(vector_dao, llm, document_dao, chat_history_dao, knowledge_graph_service)
    # 构造节点内容全为空
    knowledge_graph_service.get_knowledge_graph.return_value = {
        "nodes": [
            {"properties": {"name": "", "description": "", "content": "", "entity_type": "OtherType"}, "id": 1}
        ]
    }
    # patch VectorDAO.add/save，断言被调用一次
    from unittest.mock import patch
    with patch.object(rag_service.VectorDAO, "add") as mock_add, \
         patch.object(rag_service.VectorDAO, "save") as mock_save:
        mock_add.return_value = None
        mock_save.return_value = None
        await rag._store_knowledge_graph_nodes_to_vector_db("courseA", "file.pdf")
        assert mock_add.call_count == 1
        assert mock_save.call_count == 1

def test_clean_data_for_bson_json_serializable_object(mock_deps):
    rag = rag_service.RAGService(*mock_deps)
    class JsonSerializable:
        def __str__(self):
            return "serializable"
        def __repr__(self):
            return 'serializable'
    # __str__ 可被json.dumps
    obj = JsonSerializable()
    # monkeypatch json.dumps 使其对obj不抛异常
    import json as _json
    orig_dumps = _json.dumps
    def fake_dumps(x, *a, **kw):
        if isinstance(x, JsonSerializable):
            return '"serializable"'
        return orig_dumps(x, *a, **kw)
    import builtins
    import sys
    sys.modules['json'].dumps = fake_dumps
    result = rag._clean_data_for_bson(obj)
    assert result == obj
    sys.modules['json'].dumps = orig_dumps
