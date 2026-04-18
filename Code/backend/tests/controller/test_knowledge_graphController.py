import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from controller import knowledge_graphController

@pytest.fixture
def app():
    app = FastAPI()
    knowledge_graphController.knowledge_graph_service = MagicMock()
    app.include_router(knowledge_graphController.router)
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_get_knowledge_graph_success(client):
    knowledge_graphController.knowledge_graph_service.get_knowledge_graph.return_value = {"nodes": [], "relationships": []}
    response = client.get("/knowledge_graph?course_name=courseA&limit=10")
    assert response.status_code == 200
    assert "knowledge_graph" in response.json()

def test_get_knowledge_graph_service_none(client, app):
    knowledge_graphController.knowledge_graph_service = None
    response = client.get("/knowledge_graph?course_name=courseA&limit=10")
    assert response.status_code == 500
    assert "Service not initialized" in response.text

def test_get_knowledge_graph_service_exception(client, app):
    from controller import knowledge_graphController
    knowledge_graphController.knowledge_graph_service = MagicMock()
    knowledge_graphController.knowledge_graph_service.get_knowledge_graph.side_effect = Exception("test error")
    response = client.get("/knowledge_graph?course_name=courseA&limit=10")
    assert response.status_code == 500
    assert "test error" in response.text

def test_search_knowledge_graph_success(client):
    knowledge_graphController.knowledge_graph_service.search_knowledge_graph.return_value = {"nodes": [], "relationships": []}
    response = client.get("/knowledge_graph/search?keyword=abc&limit=10&case_sensitive=false")
    assert response.status_code == 200
    assert "result" in response.json()

def test_search_knowledge_graph_service_none(client, app):
    knowledge_graphController.knowledge_graph_service = None
    response = client.get("/knowledge_graph/search?keyword=abc&limit=10&case_sensitive=false")
    assert response.status_code == 500
    assert "Service not initialized" in response.text

def test_search_knowledge_graph_service_exception(client, app):
    from controller import knowledge_graphController
    knowledge_graphController.knowledge_graph_service = MagicMock()
    knowledge_graphController.knowledge_graph_service.search_knowledge_graph.side_effect = Exception("test error")
    response = client.get("/knowledge_graph/search?keyword=abc&limit=10&case_sensitive=false")
    assert response.status_code == 500
    assert "test error" in response.text

def test_search_knowledge_graph_by_field_success(client):
    knowledge_graphController.knowledge_graph_service.search_knowledge_graph_by_field.return_value = {"nodes": [], "relationships": []}
    response = client.get("/knowledge_graph/search/by-field?field=name&value=abc&limit=10&case_sensitive=false")
    assert response.status_code == 200
    assert "result" in response.json()

def test_search_knowledge_graph_by_field_service_none(client, app):
    knowledge_graphController.knowledge_graph_service = None
    response = client.get("/knowledge_graph/search/by-field?field=name&value=abc&limit=10&case_sensitive=false")
    assert response.status_code == 500
    assert "Service not initialized" in response.text

def test_search_knowledge_graph_by_field_service_exception(client, app):
    from controller import knowledge_graphController
    knowledge_graphController.knowledge_graph_service = MagicMock()
    knowledge_graphController.knowledge_graph_service.search_knowledge_graph_by_field.side_effect = Exception("test error")
    response = client.get("/knowledge_graph/search/by-field?field=name&value=abc&limit=10&case_sensitive=false")
    assert response.status_code == 500
    assert "test error" in response.text

def test_get_node_neighbors_by_name_success(client):
    knowledge_graphController.knowledge_graph_service.get_node_neighbors_by_name.return_value = {"nodes": [], "relationships": []}
    response = client.get("/knowledge_graph/node/by-name/test%20name/neighbors?depth=1&limit=10")
    assert response.status_code == 200
    assert "neighbors" in response.json()

def test_get_node_neighbors_by_name_service_none(client, app):
    knowledge_graphController.knowledge_graph_service = None
    response = client.get("/knowledge_graph/node/by-name/test%20name/neighbors?depth=1&limit=10")
    assert response.status_code == 500
    assert "Service not initialized" in response.text

def test_get_node_neighbors_by_name_service_exception(client, app):
    from controller import knowledge_graphController
    knowledge_graphController.knowledge_graph_service = MagicMock()
    knowledge_graphController.knowledge_graph_service.get_node_neighbors_by_name.side_effect = Exception("test error")
    response = client.get("/knowledge_graph/node/by-name/test%20name/neighbors?depth=1&limit=10")
    assert response.status_code == 500
    assert "test error" in response.text

def test_get_node_neighbors_success(client):
    knowledge_graphController.knowledge_graph_service.get_node_neighbors_by_identifier.return_value = {"nodes": [], "relationships": []}
    response = client.get("/knowledge_graph/node/4:2b1bc1df-df27-4e5a-be17-509b0d4f3578:11/neighbors?depth=1&limit=10")
    assert response.status_code == 200
    assert "neighbors" in response.json()

def test_get_node_neighbors_service_none(client, app):
    knowledge_graphController.knowledge_graph_service = None
    response = client.get("/knowledge_graph/node/4:2b1bc1df-df27-4e5a-be17-509b0d4f3578:11/neighbors?depth=1&limit=10")
    assert response.status_code == 500
    assert "Service not initialized" in response.text

def test_get_node_neighbors_service_exception(client, app):
    from controller import knowledge_graphController
    knowledge_graphController.knowledge_graph_service = MagicMock()
    knowledge_graphController.knowledge_graph_service.get_node_neighbors_by_identifier.side_effect = Exception("test error")
    response = client.get("/knowledge_graph/node/4:2b1bc1df-df27-4e5a-be17-509b0d4f3578:11/neighbors?depth=1&limit=10")
    assert response.status_code == 500
    assert "test error" in response.text 