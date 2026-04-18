import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import types
import sys
import os

# patch lightrag和neo4j依赖，防止import错误
sys.modules['lib.lightrag.types'] = types.SimpleNamespace(
    KnowledgeGraph=MagicMock(),
    KnowledgeGraphNode=MagicMock(),
    KnowledgeGraphEdge=MagicMock()
)
sys.modules['lib.lightrag.kg.neo4j_impl'] = types.SimpleNamespace(Neo4JStorage=MagicMock())
sys.modules['openai'] = MagicMock()
sys.modules['neo4j'] = types.SimpleNamespace(AsyncGraphDatabase=MagicMock())

from service.LightRAGKnowledgeGraph_generate_service import LightRAGKnowledgeGraph

@pytest.fixture
def service():
    # patch AsyncGraphDatabase.driver
    with patch('neo4j.AsyncGraphDatabase.driver', return_value=MagicMock()):
        s = LightRAGKnowledgeGraph(
            neo4j_uri='bolt://localhost:7687',
            neo4j_user='neo4j',
            neo4j_pass='test',
            deepseek_key='sk-xxx'
        )
    return s

def test_init_sets_env_and_logger(service):
    assert os.environ["NEO4J_URI"] == 'bolt://localhost:7687'
    assert os.environ["NEO4J_USERNAME"] == 'neo4j'
    assert os.environ["NEO4J_PASSWORD"] == 'test'
    assert hasattr(service, 'logger')

def test_extract_graph_from_text_success(service):
    # patch requests.post 返回模拟的 DeepSeek 响应
    with patch('requests.post') as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": '{"nodes": [{"id": "n1", "type": "Concept", "properties": {}}], "edges": [{"source_id": "n1", "target_id": "n2", "type": "CONTAINS", "properties": {}}]}'}}]
        }
        mock_post.return_value = mock_resp
        # patch Node/Edge/Graph 构造
        with patch('lib.lightrag.types.KnowledgeGraphNode', side_effect=lambda **kw: types.SimpleNamespace(**kw)), \
             patch('lib.lightrag.types.KnowledgeGraphEdge', side_effect=lambda **kw: types.SimpleNamespace(**kw)), \
             patch('lib.lightrag.types.KnowledgeGraph', side_effect=lambda nodes, edges: types.SimpleNamespace(nodes=nodes, edges=edges)):
            result = service._extract_graph_from_text('text', 'course')
            assert hasattr(result, "nodes") and hasattr(result, "edges")

def test_extract_graph_from_text_api_error(service):
    with patch('requests.post') as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = 'error'
        mock_post.return_value = mock_resp
        with pytest.raises(Exception):
            service._extract_graph_from_text('text', 'course')

def test_extract_graph_from_text_json_error(service):
    with patch('requests.post') as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": 'not a json'}}]
        }
        mock_post.return_value = mock_resp
        with pytest.raises(Exception):
            service._extract_graph_from_text('text', 'course')

def test_extract_graph_from_text_request_exception(service):
    import requests
    with patch('requests.post', side_effect=requests.exceptions.RequestException("fail")):
        service.logger = MagicMock()
        with pytest.raises(Exception) as exc:
            service._extract_graph_from_text('text', 'course')
        service.logger.error.assert_called()
        assert "DeepSeek API请求失败" in str(exc.value)

def test_split_text_into_chunks_basic(service):
    text = 'a' * 15000
    chunks = service._split_text_into_chunks(text, chunk_size=6000, overlap=1000)
    assert len(chunks) > 1
    assert all(isinstance(c, str) for c in chunks)

def test_split_text_into_chunks_empty(service):
    assert service._split_text_into_chunks('', 6000, 1000) == []

def test_split_text_into_chunks_overlap_too_large(service):
    # overlap >= chunk_size
    text = 'a' * 10000
    chunks = service._split_text_into_chunks(text, chunk_size=1000, overlap=2000)
    assert len(chunks) > 0

def test_build_and_store_graph_short_text(service):
    # patch async_init, test_connection, _extract_graph_from_text, _optimize_graph_structure, graph_store.upsert_node, graph_store.finalize
    service.async_init = AsyncMock()
    service.test_connection = AsyncMock(return_value=True)
    service._extract_graph_from_text = MagicMock(return_value=types.SimpleNamespace(nodes=[MagicMock(id='n1', labels=[], properties={})], edges=[]))
    service._optimize_graph_structure = MagicMock(side_effect=lambda g, f: g)
    service.graph_store = MagicMock()
    service.graph_store.upsert_node = AsyncMock()
    service.graph_store.finalize = AsyncMock()
    service.driver = MagicMock()
    service.link_course_root_to_subgraph_roots = AsyncMock()
    # patch logger
    service.logger = MagicMock()
    import asyncio
    asyncio.run(service.build_and_store_graph('short text', 'course', 'file', clear_existing=False, debug=False, use_chunking=False))
    service.async_init.assert_awaited()
    service.test_connection.assert_awaited()
    service.graph_store.upsert_node.assert_awaited()
    service.link_course_root_to_subgraph_roots.assert_awaited()

def fake_pydantic_model(**kwargs):
    obj = types.SimpleNamespace(**kwargs)
    def dict_method(self=obj):
        return self.__dict__
    obj.dict = dict_method
    return obj

def fake_pydantic_graph(nodes, edges):
    obj = types.SimpleNamespace(nodes=nodes, edges=edges)
    return obj

def test_build_and_store_graph_long_text(service):
    service.async_init = AsyncMock()
    service.test_connection = AsyncMock(return_value=True)
    def fake_extract(chunk, course, filename=None):
        return types.SimpleNamespace(nodes=[MagicMock(id='n1', labels=[], properties={})], edges=[MagicMock(source='n1', target='n2', type='CONTAINS', properties={})])
    service._extract_graph_from_text = MagicMock(side_effect=fake_extract)
    with patch('service.LightRAGKnowledgeGraph_generate_service.Node', side_effect=fake_pydantic_model), \
     patch('service.LightRAGKnowledgeGraph_generate_service.Edge', side_effect=fake_pydantic_model), \
     patch('service.LightRAGKnowledgeGraph_generate_service.Graph', side_effect=fake_pydantic_graph):
        service._merge_graph_with_deepseek = MagicMock(return_value={
            "nodes": [{"id": "n1", "labels": ["Concept"], "properties": {}}],
            "edges": [{"id": "e1", "source": "n1", "target": "n2", "type": "CONTAINS", "properties": {}}]
        })
        service._optimize_graph_structure = MagicMock(side_effect=lambda g, f: g)
        service.graph_store = MagicMock()
        service.graph_store.upsert_node = AsyncMock()
        service.graph_store.finalize = AsyncMock()
        service.driver = MagicMock()
        service.link_course_root_to_subgraph_roots = AsyncMock()
        service.logger = MagicMock()
        import asyncio
        long_text = 'a' * 20000
        asyncio.run(service.build_and_store_graph(long_text, 'course', 'file', clear_existing=False, debug=False, use_chunking=True))
        service._merge_graph_with_deepseek.assert_called()
        service.graph_store.upsert_node.assert_awaited()
        service.link_course_root_to_subgraph_roots.assert_awaited()

def test_build_and_store_graph_connection_fail(service):
    service.async_init = AsyncMock()
    service.test_connection = AsyncMock(return_value=False)
    service.logger = MagicMock()
    import asyncio
    asyncio.run(service.build_and_store_graph('short text', 'course', 'file', clear_existing=False, debug=False, use_chunking=False))
    service.async_init.assert_awaited()
    service.test_connection.assert_awaited()

def test_build_and_store_graph_exception(service):
    service.async_init = AsyncMock(side_effect=Exception("fail"))
    service.logger = MagicMock()
    import asyncio
    with pytest.raises(Exception):
        asyncio.run(service.build_and_store_graph('short text', 'course', 'file', clear_existing=False, debug=False, use_chunking=False))

def test_merge_graph_with_deepseek(service):
    with patch('requests.post') as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": '{"nodes": [{"id": "n1"}], "edges": [{"source": "n1", "target": "n2"}]}'}}]
        }
        mock_post.return_value = mock_resp
        result = service._merge_graph_with_deepseek([MagicMock(dict=lambda: {"id": "n1"})], [MagicMock(dict=lambda: {"source": "n1", "target": "n2"})])
        assert "nodes" in result and "edges" in result

def test_merge_graph_with_deepseek_api_error(service):
    with patch('requests.post') as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = 'error'
        mock_post.return_value = mock_resp
        with pytest.raises(Exception):
            service._merge_graph_with_deepseek([], [])

def test_optimize_graph_structure(service):
    import types
    from unittest.mock import patch, MagicMock

    def fake_pydantic_model(**kwargs):
        obj = types.SimpleNamespace(**kwargs)
        def dict_method(self=obj):
            return self.__dict__
        obj.dict = dict_method
        return obj

    with patch('service.LightRAGKnowledgeGraph_generate_service.nx') as mock_nx:
        mock_graph = MagicMock()
        mock_graph.nodes = MagicMock(return_value=["n1"])
        mock_graph.edges = MagicMock(return_value=[])
        mock_graph.add_node = MagicMock()
        mock_graph.add_edge = MagicMock()
        mock_graph.in_degree = MagicMock(return_value=0)
        mock_graph.__iter__ = lambda self=None: iter(["n1"])
        mock_graph.__contains__ = lambda self, x=None: True
        mock_nx.DiGraph.return_value = mock_graph


        with patch('service.LightRAGKnowledgeGraph_generate_service.Node', side_effect=fake_pydantic_model), \
             patch('service.LightRAGKnowledgeGraph_generate_service.Edge', side_effect=fake_pydantic_model):
            fake_node = fake_pydantic_model(id='n1', labels=[], properties={})
            graph = types.SimpleNamespace(nodes=[fake_node], edges=[])
            result = service._optimize_graph_structure(graph, 'file')
            assert result is not None

import asyncio

@pytest.mark.asyncio
def test_async_init_success(service):
    service.graph_store = MagicMock()
    service.graph_store.initialize = AsyncMock()
    service.logger = MagicMock()
    asyncio.run(service.async_init())
    service.graph_store.initialize.assert_awaited()
    service.logger.info.assert_any_call("开始初始化图谱存储...")
    service.logger.info.assert_any_call("图谱存储初始化完成")

@pytest.mark.asyncio
def test_async_init_exception(service):
    service.graph_store = MagicMock()
    service.graph_store.initialize = AsyncMock(side_effect=Exception("fail"))
    service.logger = MagicMock()
    with pytest.raises(Exception):
        asyncio.run(service.async_init())
    service.logger.error.assert_called()

@pytest.mark.asyncio
def test_close_success(service):
    driver = MagicMock()
    driver.close = AsyncMock()
    graph_store = MagicMock()
    graph_store.finalize = AsyncMock()
    service.driver = driver
    service.graph_store = graph_store
    service.logger = MagicMock()
    asyncio.run(service.close())
    driver.close.assert_awaited()
    graph_store.finalize.assert_awaited()
    service.logger.info.assert_called_with("All connections closed.")

@pytest.mark.asyncio
def test_clear_database_success(service):
    session_ctx = MagicMock()
    session_ctx.__aenter__.return_value = session_ctx
    session_ctx.run = AsyncMock()
    driver = MagicMock()
    driver.session.return_value = session_ctx
    service.driver = driver
    service.logger = MagicMock()
    asyncio.run(service.clear_database())
    session_ctx.run.assert_awaited_with("MATCH (n) DETACH DELETE n")
    service.logger.info.assert_called_with("Database cleared successfully.")

@pytest.mark.asyncio
def test_clear_database_exception(service):
    session_ctx = MagicMock()
    session_ctx.__aenter__.return_value = session_ctx
    session_ctx.run = AsyncMock(side_effect=Exception("fail"))
    driver = MagicMock()
    driver.session.return_value = session_ctx
    service.driver = driver
    service.logger = MagicMock()
    with pytest.raises(Exception):
        asyncio.run(service.clear_database())
    service.logger.error.assert_called()

@pytest.mark.asyncio
def test_test_connection_success(service):
    session_ctx = MagicMock()
    session_ctx.__aenter__.return_value = session_ctx
    session_ctx.run = AsyncMock()
    result_ctx = MagicMock()
    result_ctx.single = AsyncMock(return_value={"test": 1})
    session_ctx.run.return_value = result_ctx
    driver = MagicMock()
    driver.session.return_value = session_ctx
    service.driver = driver
    service.logger = MagicMock()
    ret = asyncio.run(service.test_connection())
    assert ret is True
    service.logger.info.assert_any_call("Neo4j连接正常")

@pytest.mark.asyncio
def test_test_connection_fail(service):
    session_ctx = MagicMock()
    session_ctx.__aenter__.return_value = session_ctx
    session_ctx.run = AsyncMock()
    result_ctx = MagicMock()
    result_ctx.single = AsyncMock(return_value={"test": 0})
    session_ctx.run.return_value = result_ctx
    driver = MagicMock()
    driver.session.return_value = session_ctx
    service.driver = driver
    service.logger = MagicMock()
    ret = asyncio.run(service.test_connection())
    assert ret is False
    service.logger.error.assert_any_call("Neo4j连接测试失败")

@pytest.mark.asyncio
def test_test_connection_exception(service):
    session_ctx = MagicMock()
    session_ctx.__aenter__.return_value = session_ctx
    session_ctx.run = AsyncMock(side_effect=Exception("fail"))
    driver = MagicMock()
    driver.session.return_value = session_ctx
    service.driver = driver
    service.logger = MagicMock()
    ret = asyncio.run(service.test_connection())
    assert ret is False
    service.logger.error.assert_called()

@pytest.mark.asyncio
def test_optimize_graph_structure_cycle_exception(service):
    import types
    from unittest.mock import patch, MagicMock
    def fake_pydantic_model(**kwargs):
        obj = types.SimpleNamespace(**kwargs)
        def dict_method(self=obj):
            return self.__dict__
        obj.dict = dict_method
        return obj
    with patch('service.LightRAGKnowledgeGraph_generate_service.nx') as mock_nx:
        mock_graph = MagicMock()
        # nodes 需要支持 __iter__ 和 __getitem__
        mock_nodes = MagicMock()
        mock_nodes.__iter__ = lambda self=None: iter(["n1"])
        mock_nodes.__getitem__ = lambda self, key: {"node": fake_pydantic_model(id=key, labels=[], properties={"course": "c"})}
        mock_graph.nodes = mock_nodes
        mock_graph.edges = MagicMock(return_value=[])
        mock_graph.add_node = MagicMock()
        mock_graph.add_edge = MagicMock()
        mock_graph.in_degree = MagicMock(return_value=0)
        mock_graph.__iter__ = lambda self=None: iter(["n1"])
        mock_graph.__contains__ = lambda self, x=None: True
        mock_nx.DiGraph.return_value = mock_graph
        mock_nx.is_directed_acyclic_graph.side_effect = [False, True]
        mock_nx.simple_cycles.side_effect = Exception("fail cycle")
        with patch('service.LightRAGKnowledgeGraph_generate_service.Node', side_effect=fake_pydantic_model), \
             patch('service.LightRAGKnowledgeGraph_generate_service.Edge', side_effect=fake_pydantic_model):
            fake_node = fake_pydantic_model(id='n1', labels=[], properties={})
            graph = types.SimpleNamespace(nodes=[fake_node], edges=[])
            service.logger = MagicMock()
            result = service._optimize_graph_structure(graph, 'file')
            service.logger.error.assert_called()

import pytest
import types
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
def test_optimize_graph_structure_cycle_main(service):
    # 模拟pydantic模型
    def fake_pydantic_model(**kwargs):
        obj = types.SimpleNamespace(**kwargs)
        obj.dict = lambda self=obj: self.__dict__
        return obj

    with patch('service.LightRAGKnowledgeGraph_generate_service.nx') as mock_nx:
        mock_graph = MagicMock()

        # nodes 支持迭代
        mock_nodes = MagicMock()
        mock_nodes.__iter__.return_value = iter(["n1", "n2"])
        mock_nodes.__getitem__.side_effect = lambda key: {"node": fake_pydantic_model(id=key, labels=[], properties={"course": "c"})}
        mock_graph.nodes = mock_nodes

        mock_graph.edges = MagicMock(return_value=[])
        mock_graph.add_node = MagicMock()
        mock_graph.add_edge = MagicMock()
        mock_graph.in_degree = MagicMock(side_effect=lambda x: 0 if x in ["n1", "n2"] else 1)
        mock_graph.__iter__.return_value = iter(["n1", "n2"])
        mock_graph.__contains__.side_effect = lambda x: x in ["n1", "n2"]

        # 关键：模拟邻接字典，支持 G[u][v]['importance'] 访问
        adjacency_dict = {
            "n1": {"n2": {"importance": 1}},  # n1 -> n2 有边，importance=1
            "n2": {"n1": {"importance": 2}},  # n2 -> n1 有边，importance=2，形成环
        }
        def getitem_side_effect(u):
            return adjacency_dict.get(u, {})
        mock_graph.__getitem__.side_effect = getitem_side_effect

        # 用来检测 remove_edge 是否被调用
        called_remove_edges = []
        def remove_edge_side_effect(u, v):
            called_remove_edges.append((u, v))
        mock_graph.remove_edge.side_effect = remove_edge_side_effect

        mock_nx.DiGraph.return_value = mock_graph
        # 第一次有环，第二次无环，确保 while 循环执行一次
        mock_nx.is_directed_acyclic_graph.side_effect = [False, True]

        # simple_cycles 返回一个环
        mock_nx.simple_cycles.side_effect = lambda G: [["n1", "n2"]]

        with patch('service.LightRAGKnowledgeGraph_generate_service.Node', side_effect=fake_pydantic_model), \
             patch('service.LightRAGKnowledgeGraph_generate_service.Edge', side_effect=fake_pydantic_model):

            fake_node1 = fake_pydantic_model(id='n1', labels=[], properties={})
            fake_node2 = fake_pydantic_model(id='n2', labels=[], properties={})
            test_graph = types.SimpleNamespace(nodes=[fake_node1, fake_node2], edges=[])

            service.logger = MagicMock()

            result = service._optimize_graph_structure(test_graph, 'file')

            # 打印调试调用情况
            print("remove_edge calls:", called_remove_edges)

            # 断言 remove_edge 被调用过
            assert len(called_remove_edges) > 0, "Expected remove_edge to be called, but it was not called."
            assert result is not None

@pytest.mark.asyncio
def test_optimize_graph_structure_importance_and_remove_restore(service):
    import types
    from unittest.mock import patch, MagicMock
    def fake_pydantic_model(**kwargs):
        obj = types.SimpleNamespace(**kwargs)
        obj.dict = lambda self=obj: self.__dict__
        return obj
    with patch('service.LightRAGKnowledgeGraph_generate_service.nx') as mock_nx:
        mock_graph = MagicMock()
        # nodes 支持迭代
        mock_nodes = MagicMock()
        mock_nodes.__iter__.return_value = iter(["n1", "n2"])
        mock_nodes.__getitem__.side_effect = lambda key: {"node": fake_pydantic_model(id=key, labels=[], properties={"course": "c"})}
        mock_graph.nodes = mock_nodes
        # edges: 只需存在即可
        mock_graph.edges = MagicMock(return_value=[("n1", "n2", {"importance": "not_an_int"})])
        mock_graph.add_node = MagicMock()
        mock_graph.add_edge = MagicMock()
        mock_graph.in_degree = MagicMock(side_effect=lambda x: 0 if x in ["n1", "n2"] else 1)
        mock_graph.__iter__.return_value = iter(["n1", "n2"])
        mock_graph.__contains__.side_effect = lambda x: x in ["n1", "n2"]
        # G[u][v] 支持 importance
        adjacency_dict = {
            "n1": {"n2": {"importance": 1}},
            "n2": {"n1": {"importance": 2}},
        }
        def getitem_side_effect(u):
            return adjacency_dict.get(u, {})
        mock_graph.__getitem__.side_effect = getitem_side_effect
        # remove_edge/add_edge/has_path
        mock_graph.remove_edge = MagicMock()
        mock_graph.add_edge = MagicMock()
        mock_nx.DiGraph.return_value = mock_graph
        mock_nx.has_path.return_value = True
        mock_nx.is_directed_acyclic_graph.return_value = True
        with patch('service.LightRAGKnowledgeGraph_generate_service.Node', side_effect=fake_pydantic_model), \
             patch('service.LightRAGKnowledgeGraph_generate_service.Edge', side_effect=fake_pydantic_model):
            fake_node1 = fake_pydantic_model(id='n1', labels=[], properties={})
            fake_node2 = fake_pydantic_model(id='n2', labels=[], properties={})
            test_graph = types.SimpleNamespace(nodes=[fake_node1, fake_node2], edges=[types.SimpleNamespace(source="n1", target="n2", properties={"importance": "not_an_int"})])
            service.logger = MagicMock()
            result = service._optimize_graph_structure(test_graph, 'file')
            # importance 不是 int，except 分支赋值为1
            mock_graph.add_edge.assert_any_call("n1", "n2", edge=test_graph.edges[0], importance=1)
            mock_graph.remove_edge.assert_called()
            mock_graph.add_edge.assert_called()
            mock_nx.has_path.assert_called()
            assert result is not None

@pytest.mark.asyncio
def test_link_course_root_to_subgraph_roots(service):
    # mock session context
    session_ctx = MagicMock()
    session_ctx.__aenter__.return_value = session_ctx
    # 第一次 run 返回 sub_root_id 结果
    result_ctx = MagicMock()
    result_ctx.data = AsyncMock(return_value=[{"sub_root_id": "file_root_1"}, {"sub_root_id": "file_root_2"}])
    session_ctx.run = AsyncMock(side_effect=[result_ctx, None, None])  # 第一次 run 查roots，后面 run link
    driver = MagicMock()
    driver.session.return_value = session_ctx
    service.driver = driver
    service.logger = MagicMock()
    import asyncio
    asyncio.run(service.link_course_root_to_subgraph_roots("courseA"))
    # 断言 cypher 被执行
    assert session_ctx.run.await_count >= 3
    service.logger.info.assert_called()