from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Path
from service.knowledge_graph_service import KnowledgeGraphService
from dto.schemas import (
    KnowledgeGraphResponse,
    SearchKnowledgeGraphResponse,
    NodeNeighborsResponse
)

router = APIRouter(
    prefix="/knowledge_graph",
    tags=["知识图谱"],
    responses={404: {"description": "未找到"}, 500: {"description": "服务器内部错误"}}
)
knowledge_graph_service: Optional[KnowledgeGraphService] = None

@router.get("", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(
    course_name: str = Query(..., description="课程名，返回该课程的知识图谱"),
    limit: int = Query(default=100, description="限制返回的节点数量", ge=1, le=1000)
):
    """
    获取指定课程的知识图谱节点和关系
    参数:
    - course_name: 课程名，返回该课程的知识图谱
    - limit: 限制返回的节点数量，默认100，范围1-1000
    
    返回:
    ```json
    {
        "knowledge_graph": {
            "nodes": [
                {
                    "id": "节点ID",
                    "labels": ["节点标签"],
                    "properties": {
                        "name": "节点名称",
                        "entity_type": "节点类型",
                        "course": "所属课程",
                        "entity_id": "节点唯一标识符",
                        "description": "节点描述",
                        "content": "节点内容",
                        "importance": "重要性",
                        "category": "类别"
                    }
                }
            ],
            "relationships": [
                {
                    "id": "关系ID",
                    "type": "关系类型",
                    "source": "起始节点ID",
                    "target": "目标节点ID",
                    "properties": {}
                }
            ]
        }
    }
    ```
    """
    if not knowledge_graph_service:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        knowledge_graph = knowledge_graph_service.get_knowledge_graph(course_name=course_name, limit=limit)
        return {"knowledge_graph": knowledge_graph}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=SearchKnowledgeGraphResponse)
async def search_knowledge_graph(
    keyword: str = Query(..., description="搜索关键词，将在节点的name字段中搜索"),
    limit: int = Query(default=100, description="限制返回的节点数量", ge=1, le=1000),
    case_sensitive: bool = Query(default=False, description="是否区分大小写")
):
    """
    按关键词搜索知识图谱中的节点
    
    参数:
    - keyword: 搜索关键词，将在节点的name字段中搜索
    - limit: 限制返回的节点数量，默认100，范围1-1000
    - case_sensitive: 是否区分大小写，默认False
    
    示例:
    ```
    GET /knowledge_graph/search?keyword=Exception&limit=10&case_sensitive=false
    ```
    
    返回:
    ```json
    {
        "result": {
            "nodes": [
                {
                    "id": "节点ID",
                    "labels": ["节点标签"],
                    "properties": {
                        "name": "节点名称",
                        "entity_type": "节点类型",
                        "course": "所属课程",
                        "entity_id": "节点唯一标识符",
                        "description": "节点描述",
                        "content": "节点内容",
                        "importance": "重要性",
                        "category": "类别"
                    }
                }
            ],
            "relationships": [
                {
                    "id": "关系ID",
                    "type": "关系类型",
                    "source": "起始节点ID",
                    "target": "目标节点ID",
                    "properties": {}
                }
            ]
        }
    }
    ```
    """
    if not knowledge_graph_service:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        result = knowledge_graph_service.search_knowledge_graph(
            keyword=keyword,
            limit=limit,
            case_sensitive=case_sensitive
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/by-field", response_model=SearchKnowledgeGraphResponse)
async def search_knowledge_graph_by_field(
    field: str = Query(..., description="要搜索的字段名称（例如：course, entity_type等）"),
    value: str = Query(..., description="字段的值"),
    limit: int = Query(default=100, description="限制返回的节点数量", ge=1, le=1000),
    case_sensitive: bool = Query(default=False, description="是否区分大小写")
):
    """
    按字段值搜索知识图谱中的节点
    
    参数:
    - field: 要搜索的字段名称，可选值：name, course, entity_type, entity_id
    - value: 字段的值
    - limit: 限制返回的节点数量，默认100，范围1-1000
    - case_sensitive: 是否区分大小写，默认False
    
    示例:
    ```
    GET /knowledge_graph/search/by-field?field=course&value=ICS&limit=50
    GET /knowledge_graph/search/by-field?field=entity_type&value=Concept
    ```
    
    返回:
    ```json
    {
        "result": {
            "nodes": [
                {
                    "id": "节点ID",
                    "labels": ["节点标签"],
                    "properties": {
                        "name": "节点名称",
                        "entity_type": "节点类型",
                        "course": "所属课程",
                        "entity_id": "节点唯一标识符",
                        "description": "节点描述",
                        "content": "节点内容",
                        "importance": "重要性",
                        "category": "类别"
                    }
                }
            ],
            "relationships": [
                {
                    "id": "关系ID",
                    "type": "关系类型",
                    "source": "起始节点ID",
                    "target": "目标节点ID",
                    "properties": {}
                }
            ]
        }
    }
    ```
    """
    if not knowledge_graph_service:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        result = knowledge_graph_service.search_knowledge_graph_by_field(
            field=field,
            value=value,
            limit=limit,
            case_sensitive=case_sensitive
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/node/by-name/{name}/neighbors", response_model=NodeNeighborsResponse)
async def get_node_neighbors_by_name(
    name: str = Path(..., description="节点的name属性值，URL中的空格应该编码为%20", title="Node Name"),
    depth: int = Query(default=1, description="遍历深度", ge=1, le=3),
    limit: int = Query(default=50, description="限制返回的节点数量", ge=1, le=500)
):
    """
    通过节点名称获取其邻居节点
    
    参数:
    - name: 节点的name属性值（路径参数）。如果名称包含空格，在URL中应该将空格编码为%20
    - depth: 遍历深度，默认1，范围1-3
    - limit: 限制返回的节点数量，默认50，范围1-500
    
    示例:
    ```
    GET /knowledge_graph/node/by-name/Exception%20handling/neighbors?depth=2&limit=100
    ```
    
    返回:
    ```json
    {
        "neighbors": {
            "nodes": [
                {
                    "id": "节点ID",
                    "labels": ["节点标签"],
                    "properties": {
                        "name": "节点名称",
                        "entity_type": "节点类型",
                        "course": "所属课程",
                        "entity_id": "节点唯一标识符",
                        "description": "节点描述",
                        "content": "节点内容",
                        "importance": "重要性",
                        "category": "类别"
                    }
                }
            ],
            "relationships": [
                {
                    "id": "关系ID",
                    "type": "关系类型",
                    "source": "起始节点ID",
                    "target": "目标节点ID",
                    "properties": {}
                }
            ]
        }
    }
    ```
    
    说明:
    - depth=1 表示只返回直接相连的节点
    - depth=2 表示返回直接相连的节点及其相连的节点
    - depth=3 表示再往外扩展一层
    - 如果节点名称包含空格，请使用%20代替空格，例如："Data%20forwarding"
    """
    if not knowledge_graph_service:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        neighbors = knowledge_graph_service.get_node_neighbors_by_name(
            name=name,
            depth=depth,
            limit=limit
        )
        return {"neighbors": neighbors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/node/{node_identifier}/neighbors", response_model=NodeNeighborsResponse)
async def get_node_neighbors(
    node_identifier: str = Path(..., description="节点的完整标识符（例如：4:2b1bc1df-df27-4e5a-be17-509b0d4f3578:11）"),
    depth: int = Query(default=1, description="遍历深度", ge=1, le=3),
    limit: int = Query(default=50, description="限制返回的节点数量", ge=1, le=500)
):
    """
    通过节点标识符获取其邻居节点
    
    参数:
    - node_identifier: 节点的完整标识符（路径参数），格式如：4:2b1bc1df-df27-4e5a-be17-509b0d4f3578:11
    - depth: 遍历深度，默认1，范围1-3
    - limit: 限制返回的节点数量，默认50，范围1-500
    
    示例:
    ```
    GET /knowledge_graph/node/4:2b1bc1df-df27-4e5a-be17-509b0d4f3578:11/neighbors?depth=2
    ```
    
    返回:
    ```json
    {
        "neighbors": {
            "nodes": [
                {
                    "id": "节点ID",
                    "labels": ["节点标签"],
                    "properties": {
                        "name": "节点名称",
                        "entity_type": "节点类型",
                        "course": "所属课程",
                        "entity_id": "节点唯一标识符",
                        "description": "节点描述",
                        "content": "节点内容",
                        "importance": "重要性",
                        "category": "类别"
                    }
                }
            ],
            "relationships": [
                {
                    "id": "关系ID",
                    "type": "关系类型",
                    "source": "起始节点ID",
                    "target": "目标节点ID",
                    "properties": {}
                }
            ]
        }
    }
    ```
    
    说明:
    - depth=1 表示只返回直接相连的节点
    - depth=2 表示返回直接相连的节点及其相连的节点
    - depth=3 表示再往外扩展一层
    """
    if not knowledge_graph_service:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        neighbors = knowledge_graph_service.get_node_neighbors_by_identifier(
            node_identifier=node_identifier,
            depth=depth,
            limit=limit
        )
        return {"neighbors": neighbors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
