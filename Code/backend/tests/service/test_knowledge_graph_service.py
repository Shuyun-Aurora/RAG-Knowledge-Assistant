import pytest
from unittest.mock import MagicMock, patch
from service.knowledge_graph_service import KnowledgeGraphService
import types
import logging

@pytest.fixture
def mock_dao():
    dao = MagicMock()
    return dao

@pytest.fixture
def mock_vector_dao():
    vdao = MagicMock()
    return vdao

@pytest.fixture
def service(mock_dao, mock_vector_dao):
    return KnowledgeGraphService(mock_dao, mock_vector_dao)

def test_get_knowledge_graph(service, mock_dao):
    mock_dao.get_knowledge_graph.return_value = {"nodes": [], "relationships": []}
    result = service.get_knowledge_graph("courseA", 10)
    assert "nodes" in result

def test_search_knowledge_graph_success(service, mock_dao):
    mock_dao.search_knowledge_graph.return_value = {"nodes": []}
    result = service.search_knowledge_graph("kw", 5, False)
    assert "nodes" in result

def test_search_knowledge_graph_exception(service, mock_dao):
    mock_dao.search_knowledge_graph.side_effect = Exception("fail")
    with pytest.raises(Exception) as e:
        service.search_knowledge_graph("kw", 5, False)
    assert "搜索知识图谱失败" in str(e.value)

def test_get_node_neighbors_success(service, mock_dao):
    mock_dao.get_node_neighbors.return_value = {"nodes": []}
    result = service.get_node_neighbors(1, 1, 10)
    assert "nodes" in result

def test_get_node_neighbors_exception(service, mock_dao):
    mock_dao.get_node_neighbors.side_effect = Exception("fail")
    with pytest.raises(Exception) as e:
        service.get_node_neighbors(1, 1, 10)
    assert "获取节点邻居失败" in str(e.value)

def test_close_success(service, mock_dao):
    service.close()
    mock_dao.close.assert_called()

def test_close_exception(service, mock_dao):
    mock_dao.close.side_effect = Exception("fail")
    with pytest.raises(Exception) as e:
        service.close()
    assert "关闭知识图谱连接失败" in str(e.value)

def test_search_knowledge_graph_by_field_success(service, mock_dao):
    mock_dao.search_knowledge_graph_by_field.return_value = {"nodes": []}
    result = service.search_knowledge_graph_by_field("field", "val", 5, False)
    assert "nodes" in result

def test_search_knowledge_graph_by_field_exception(service, mock_dao):
    mock_dao.search_knowledge_graph_by_field.side_effect = Exception("fail")
    with pytest.raises(Exception) as e:
        service.search_knowledge_graph_by_field("field", "val", 5, False)
    assert "按字段搜索知识图谱失败" in str(e.value)

@pytest.mark.asyncio
async def test_search_related_nodes_success(service):
    service._high_precision_vector_search = MagicMock(return_value=[{"id": "1", "similarity": 0.9}])
    service._get_node_details = MagicMock(return_value=[{"id": "1"}])
    service._get_neighbor_nodes = MagicMock(return_value=([{"id": "2"}], [{"source_id": "1", "target_id": "2", "type": "rel", "properties": {}}]))
    service._build_enhanced_context = MagicMock(return_value="context")
    result = await service.search_related_nodes("q", "c")
    assert "nodes" in result
    assert "context" in result

@pytest.mark.asyncio
async def test_search_related_nodes_exception(service):
    service._high_precision_vector_search = MagicMock(side_effect=Exception("fail"))
    result = await service.search_related_nodes("q", "c")
    assert result["nodes"] == []
    assert "error" in result

@pytest.mark.asyncio
async def test_search_related_nodes_no_related_nodes(service):
    # mock _high_precision_vector_search 返回空列表（async）
    async def fake_high_precision_vector_search(*a, **kw):
        return []
    service._high_precision_vector_search = fake_high_precision_vector_search
    # 其它依赖不应被调用，但可 mock
    service._get_node_details = MagicMock()
    service._get_neighbor_nodes = MagicMock()
    service._build_enhanced_context = MagicMock()
    result = await service.search_related_nodes("q", "c")
    assert result["nodes"] == []
    assert result["edges"] == []
    assert result["context"] == ""
    assert result["search_info"] == "相似度阈值过高"

@pytest.mark.asyncio
async def test__high_precision_vector_search_success(service):
    mock_kg_vector_dao = MagicMock()
    mock_kg_vector_dao.search.return_value = [(types.SimpleNamespace(metadata={"type": "knowledge_graph_node", "node_id": "1", "node_name": "n"}, page_content="c"), 0.1)]
    result = await service._high_precision_vector_search("q", "c", 1, 0.1, mock_kg_vector_dao)
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test__high_precision_vector_search_exception(service):
    mock_kg_vector_dao = MagicMock()
    mock_kg_vector_dao.search.side_effect = Exception("fail")
    result = await service._high_precision_vector_search("q", "c", 1, 0.1, mock_kg_vector_dao)
    assert result == []

@pytest.mark.asyncio
async def test__vector_search_nodes(service):
    async def fake_high_precision_vector_search(*a, **kw):
        return [{"id": "1"}]
    service._high_precision_vector_search = fake_high_precision_vector_search
    result = await service._vector_search_nodes("q", "c", 1)
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test__get_node_details_success(service, mock_dao):
    mock_dao.get_node_by_id.return_value = {"id": "1"}
    result = await service._get_node_details(["1"])
    assert result == [{"id": "1"}]

@pytest.mark.asyncio
async def test__get_node_details_exception(service, mock_dao):
    mock_dao.get_node_by_id.side_effect = Exception("fail")
    result = await service._get_node_details(["1"])
    assert result == []

@pytest.mark.asyncio
async def test__get_neighbor_nodes_success(service, mock_dao):
    mock_dao.get_node_neighbors.return_value = {"nodes": [{"id": "2"}], "relationships": [{"id": "e1"}]}
    result = await service._get_neighbor_nodes(["1"], 1)
    assert isinstance(result, tuple)
    assert isinstance(result[0], list)
    assert isinstance(result[1], list)

@pytest.mark.asyncio
async def test__get_neighbor_nodes_exception(service, mock_dao):
    mock_dao.get_node_neighbors.side_effect = Exception("fail")
    result = await service._get_neighbor_nodes(["1"], 1)
    assert result == ([], [])

def test__build_enhanced_context_success(service):
    nodes = [{"id": "1", "name": "n", "type": "t", "description": "d", "content": "c"}]
    edges = [{"source_id": "1", "target_id": "2", "type": "rel", "properties": {}}]
    related_nodes = [{"id": "1", "similarity": 0.9}]
    result = service._build_enhanced_context(nodes, edges, related_nodes)
    assert isinstance(result, str)

def test__build_enhanced_context_exception(service):
    # 传入非法数据触发except
    result = service._build_enhanced_context(None, None, None)
    assert "知识图谱信息构建失败" in result

def test__build_context(service):
    nodes = [{"id": "1"}]
    edges = []
    result = service._build_context(nodes, edges)
    assert isinstance(result, str)

def test_delete_nodes_by_filename_success(service, mock_dao):
    mock_dao.delete_nodes_by_filename.return_value = {"success": True}
    result = service.delete_nodes_by_filename("f", "c")
    assert result["success"]

def test_delete_nodes_by_filename_exception(service, mock_dao):
    mock_dao.delete_nodes_by_filename.side_effect = Exception("fail")
    with pytest.raises(Exception) as e:
        service.delete_nodes_by_filename("f", "c")
    assert "删除知识图谱节点失败" in str(e.value)

def test_delete_kg_vectors_by_filename_success(service, mock_dao):
    with patch("repository.embedding_repository.QwenEmbeddings"), \
         patch("config.settings.settings", type("S", (), {"DASHSCOPE_API_KEY": "k"})()), \
         patch("dao.vector_dao.VectorDAO") as MockVectorDAO:
        mock_kg_vector_dao = MockVectorDAO.return_value
        mock_kg_vector_dao.delete_by_source.return_value = 1
        mock_kg_vector_dao._get_all_documents.return_value = {"metadatas": [], "ids": []}
        mock_kg_vector_dao.add.return_value = None
        mock_kg_vector_dao.save.return_value = None
        mock_dao.get_knowledge_graph.return_value = {"nodes": []}
        service.knowledge_graph_dao = mock_dao
        result = service.delete_kg_vectors_by_filename("f", "c")
        assert result["success"]

def test_delete_kg_vectors_by_filename_exception(service):
    with patch("repository.embedding_repository.QwenEmbeddings"), \
         patch("config.settings.settings", type("S", (), {"DASHSCOPE_API_KEY": "k"})()), \
         patch("dao.vector_dao.VectorDAO") as MockVectorDAO:
        mock_kg_vector_dao = MockVectorDAO.return_value
        mock_kg_vector_dao.delete_by_source.side_effect = Exception("fail")
        result = service.delete_kg_vectors_by_filename("f", "c")
        assert not result["success"]
        assert "删除知识图谱向量失败" in result["message"]

def test_delete_kg_vectors_by_filename_course_related_ids(service, mock_dao):
    # patch QwenEmbeddings, VectorDAO, settings
    with patch("repository.embedding_repository.QwenEmbeddings"), \
         patch("config.settings.settings", type("S", (), {"DASHSCOPE_API_KEY": "k"})()), \
         patch("dao.vector_dao.VectorDAO") as MockVectorDAO:
        mock_kg_vector_dao = MockVectorDAO.return_value
        # 构造 metadatas/ids 有课程相关数据
        mock_kg_vector_dao._get_all_documents.return_value = {
            "metadatas": [{"course": "c", "source": "knowledge_graph_c", "node_type": "NotCourseRoot"}],
            "ids": ["id1"]
        }
        mock_kg_vector_dao.delete_by_source.return_value = 1
        mock_kg_vector_dao.add.return_value = None
        mock_kg_vector_dao.save.return_value = None
        # mock get_knowledge_graph 返回 CourseRoot 节点
        mock_dao.get_knowledge_graph.return_value = {
            "nodes": [{
                "id": "cr1",
                "labels": ["CourseRoot"],
                "properties": {"name": "n", "description": "d", "content": "c", "importance": "i"}
            }]
        }
        service.knowledge_graph_dao = mock_dao
        result = service.delete_kg_vectors_by_filename("f", "c")
        assert result["success"]
        # 断言 delete_by_source、add、save 被调用
        assert mock_kg_vector_dao.delete_by_source.call_count >= 2
        mock_kg_vector_dao.add.assert_called()
        mock_kg_vector_dao.save.assert_called()

def test_add_node(service, mock_dao):
    service.add_node({"id": 1})
    mock_dao.add_node.assert_called() 

@pytest.mark.asyncio
async def test_search_related_nodes_main_flow(service):
    # mock _high_precision_vector_search 返回非空
    async def fake_high_precision_vector_search(*a, **kw):
        return [{"id": "1", "similarity": 0.9}]
    service._high_precision_vector_search = fake_high_precision_vector_search

    # mock _get_node_details 返回节点详情
    async def fake_get_node_details(node_ids):
        return [{"id": "1"}]
    service._get_node_details = fake_get_node_details

    # mock _get_neighbor_nodes 返回邻居节点和边
    async def fake_get_neighbor_nodes(node_ids, depth):
        return ([{"id": "2"}], [{"source_id": "1", "target_id": "2", "type": "rel", "properties": {}}])
    service._get_neighbor_nodes = fake_get_neighbor_nodes

    # mock _build_enhanced_context
    service._build_enhanced_context = MagicMock(return_value="context")

    result = await service.search_related_nodes("q", "c")
    assert result["nodes"] == [{"id": "1"}, {"id": "2"}]
    assert result["edges"] == [{"source_id": "1", "target_id": "2", "type": "rel", "properties": {}}]
    assert result["context"] == "context"
    assert result["related_count"] == 1
    assert result["total_nodes"] == 2
    assert result["total_edges"] == 1
    assert result["search_info"] == "向量检索1个节点，图扩展后2个节点"