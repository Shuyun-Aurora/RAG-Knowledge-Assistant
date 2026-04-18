import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeGraphRepository:
    def __init__(self, uri: str, username: str, password: str):
        """
        初始化Neo4j连接
        :param uri: neo4j://127.0.0.1:7687
        :param username: neo4j
        :param password: 12345678
        """
        self.target_database = "neo4j"
        # 确保URI不包含数据库名称
        if "/" in uri.split("://")[1]:
            uri = uri.split("/")[0]
        
        logger.info(f"Connecting to Neo4j at {uri}")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            
            # 直接使用目标数据库
            with self.driver.session(database=self.target_database) as session:
                result = session.run("RETURN 1 as test")
                result.single()
                logger.info(f"Successfully connected to database '{self.target_database}'")
            
        except ClientError as e:
            if "database does not exist" in str(e):
                logger.error(f"Database '{self.target_database}' does not exist. Please create it first using Neo4j Browser or neo4j-admin.")
            elif "not have permission" in str(e):
                logger.error("Permission denied. Make sure the user has admin rights to create databases.")
            logger.error(f"Neo4j client error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise

    def close(self):
        """关闭数据库连接"""
        try:
            self.driver.close()
            logger.info("Neo4j connection closed")
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {str(e)}")
            raise

    def ensure_course_root(self, course_name: str) -> Dict[str, Any]:
        try:
            with self.driver.session(database=self.target_database) as session:
                result = session.run(
                    """
                    MERGE (root:base:CourseRoot {entity_id: $course_root_id})
                    ON CREATE SET
                        root.entity_type = 'CourseRoot',
                        root.course = $course_name,
                        root.name = $course_name,
                        root.description = $course_description,
                        root.category = 'CourseRoot',
                        root.content = $course_content
                    RETURN root.entity_id AS entity_id, root.course AS course
                    """,
                    course_root_id=f"{course_name}_root",
                    course_name=course_name,
                    course_description=f"课程{course_name}的根节点",
                    course_content=f"课程{course_name}的根节点",
                )
                record = result.single()
                return {
                    "success": True,
                    "entity_id": record["entity_id"] if record else f"{course_name}_root",
                    "course": record["course"] if record else course_name,
                }
        except Exception as e:
            logger.error(f"确保 CourseRoot 失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def ensure_course_root_and_link_file_root(self, course_name: str, filename: str) -> Dict[str, Any]:
        try:
            with self.driver.session(database=self.target_database) as session:
                result = session.run(
                    """
                    MERGE (root:base:CourseRoot {entity_id: $course_root_id})
                    ON CREATE SET
                        root.entity_type = 'CourseRoot',
                        root.course = $course_name,
                        root.name = $course_name,
                        root.description = $course_description,
                        root.category = 'CourseRoot',
                        root.content = $course_content
                    WITH root
                    MATCH (file:FileRoot {course: $course_name, name: $filename})
                    MERGE (root)-[r:CONTAINS]->(file)
                    SET r.description = '课程根节点包含文件知识图谱根节点',
                        r.strength = 'Strong',
                        r.direction = 'CONTAINS'
                    RETURN root.entity_id AS course_root_id, file.entity_id AS file_root_id
                    """,
                    course_root_id=f"{course_name}_root",
                    course_name=course_name,
                    filename=filename,
                    course_description=f"课程{course_name}的根节点",
                    course_content=f"课程{course_name}的根节点",
                )
                record = result.single()
                if not record:
                    return {
                        "success": False,
                        "message": f"未找到课程 '{course_name}' 下文件 '{filename}' 的 FileRoot 节点",
                    }
                return {
                    "success": True,
                    "course_root_id": record["course_root_id"],
                    "file_root_id": record["file_root_id"],
                }
        except Exception as e:
            logger.error(f"确保 CourseRoot 并连接 FileRoot 失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def delete_nodes_by_filename(self, filename: str, course_name: str) -> Dict[str, Any]:
        """
        根据文件名删除知识图谱中的相关节点及其所有子节点
        
        :param filename: 文件名
        :param course_name: 课程名
        :return: 删除结果
        """
        try:
            with self.driver.session(database=self.target_database) as session:
                # 首先找到与文件名相关的FileRoot节点
                file_root_query = """
                MATCH (n:FileRoot)
                WHERE n.name = $filename AND n.course = $course_name
                RETURN id(n) as root_id
                """
                
                root_result = session.run(file_root_query, filename=filename, course_name=course_name)
                root_record = root_result.single()
                
                if not root_record:
                    logger.warning(f"未找到文件名 '{filename}' 的FileRoot节点")
                    return {"success": False, "message": f"未找到文件名 '{filename}' 的FileRoot节点", "deleted_nodes": 0}
                
                root_id = root_record["root_id"]
                
                # 找到所有从该FileRoot节点可达的节点（包括FileRoot本身），但排除CourseRoot节点
                reachable_nodes_query = """
                MATCH (root:FileRoot)-[*0..]->(n)
                WHERE id(root) = $root_id AND NOT ('CourseRoot' IN labels(n))
                RETURN DISTINCT id(n) as node_id
                """
                
                reachable_result = session.run(reachable_nodes_query, root_id=root_id)
                node_ids = [record["node_id"] for record in reachable_result]
                
                if not node_ids:
                    logger.warning(f"未找到从FileRoot节点 {root_id} 可达的节点")
                    return {"success": False, "message": "未找到可达节点", "deleted_nodes": 0}
                
                # 删除所有相关节点及其关系
                delete_query = """
                MATCH (n)
                WHERE id(n) IN $node_ids
                DETACH DELETE n
                """
                
                delete_result = session.run(delete_query, node_ids=node_ids)
                summary = delete_result.consume()
                
                deleted_nodes = summary.counters.nodes_deleted
                deleted_relationships = summary.counters.relationships_deleted
                
                logger.info(f"删除 {deleted_nodes} 个节点和 {deleted_relationships} 个关系")
                
                return {
                    "success": True,
                    "message": f"成功删除文件名 '{filename}' 相关的知识图谱节点",
                    "deleted_nodes": deleted_nodes,
                    "deleted_relationships": deleted_relationships,
                    "node_ids": node_ids
                }
                
        except Exception as e:
            logger.error(f"删除知识图谱节点失败: {str(e)}")
            return {"success": False, "message": f"删除知识图谱节点失败: {str(e)}", "deleted_nodes": 0}

    def get_knowledge_graph(self, course_name: str, limit: int = 100) -> Dict[str, Any]:
        """
        获取指定课程的知识图谱数据
        :param course_name: 课程名
        :param limit: 限制返回的节点数量
        :return: 知识图谱数据
        """
        try:
            with self.driver.session(database=self.target_database) as session:
                # 查询指定课程的节点和关系
                nodes_result = session.run(
                    """
                    MATCH (n)
                    WHERE n.course = $course_name OR n.properties.course = $course_name
                    RETURN DISTINCT
                        id(n) as id,
                        labels(n) as labels,
                        properties(n) as properties
                    LIMIT $limit
                    """,
                    course_name=course_name,
                    limit=limit
                )
                nodes = []
                node_ids = []
                for record in nodes_result:
                    node = {
                        "id": record["id"],
                        "labels": record["labels"],
                        "properties": record["properties"]
                    }
                    nodes.append(node)
                    node_ids.append(record["id"])
                
                # 查询这些节点之间的关系
                relationships_result = session.run(
                    """
                    MATCH (n)-[r]->(m)
                    WHERE id(n) IN $node_ids AND id(m) IN $node_ids
                    RETURN DISTINCT
                        id(r) as id,
                        type(r) as type,
                        id(startNode(r)) as source,
                        id(endNode(r)) as target,
                        properties(r) as properties
                    """,
                    node_ids=node_ids
                )
                relationships = []
                for record in relationships_result:
                    relationship = {
                        "id": record["id"],
                        "type": record["type"],
                        "source": record["source"],
                        "target": record["target"],
                        "properties": record["properties"]
                    }
                    relationships.append(relationship)
                
                return {
                    "nodes": nodes,
                    "relationships": relationships
                }
        except Exception as e:
            raise Exception(f"获取知识图谱失败: {str(e)}")

    def search_knowledge_graph(self, keyword: str, limit: int = 100, case_sensitive: bool = False) -> Dict[str, Any]:
        """
        根据关键词搜索知识图谱
        :param keyword: 搜索关键词（将在name字段中搜索）
        :param limit: 限制返回的节点数量
        :param case_sensitive: 是否区分大小写
        :return: 包含匹配节点和相关关系的字典
        """
        try:
            with self.driver.session(database=self.target_database) as session:
                # 搜索匹配关键词的节点（只在name字段中搜索）
                query = """
                    MATCH (n)
                    WHERE {where_clause}
                    RETURN DISTINCT
                        id(n) as id,
                        labels(n) as labels,
                        properties(n) as properties
                    LIMIT $limit
                """
                
                # 根据case_sensitive参数决定使用哪种匹配方式
                where_clause = "n.name CONTAINS $keyword" if case_sensitive else "toLower(n.name) CONTAINS toLower($keyword)"
                query = query.format(where_clause=where_clause)
                
                nodes_result = session.run(
                    query,
                    keyword=keyword,
                    limit=limit
                )

                nodes = []
                for record in nodes_result:
                    node = {
                        "id": record["id"],
                        "labels": record["labels"],
                        "properties": record["properties"]
                    }
                    nodes.append(node)

                # 获取匹配节点之间的关系
                relationships_result = session.run(
                    """
                    MATCH (n)-[r]->(m)
                    WHERE id(n) IN $node_ids AND id(m) IN $node_ids
                    RETURN DISTINCT
                        id(r) as id,
                        type(r) as type,
                        properties(r) as properties,
                        id(startNode(r)) as source,
                        id(endNode(r)) as target
                    """,
                    node_ids=[node["id"] for node in nodes]
                )

                relationships = []
                for record in relationships_result:
                    relationship = {
                        "id": record["id"],
                        "type": record["properties"].get("type", record["type"]),
                        "source": record["source"],
                        "target": record["target"],
                        "properties": {k: v for k, v in record["properties"].items() if k != "type"}
                    }
                    relationships.append(relationship)

                return {
                    "nodes": nodes,
                    "relationships": relationships
                }

        except Neo4jError as e:
            logger.error(f"Neo4j search error: {str(e)}")
            raise Exception(f"Neo4j搜索错误: {str(e)}")

    def get_node_neighbors(self, node_id: int, depth: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        获取指定节点的邻居节点和关系
        :param node_id: 节点ID
        :param depth: 遍历深度
        :param limit: 限制返回的节点数量
        :return: 包含邻居节点和关系的字典
        """
        try:
            with self.driver.session(database=self.target_database) as session:
                # 获取中心节点及其邻居，严格限制深度
                if depth == 1:
                    # 只获取直接邻居（深度1）
                    result = session.run(
                        """
                        MATCH (n)-[r]-(m)
                        WHERE id(n) = $node_id
                        RETURN COLLECT(DISTINCT {
                            id: id(m),
                            labels: labels(m),
                            properties: properties(m)
                        }) as nodes,
                        COLLECT(DISTINCT {
                            id: id(r),
                            type: type(r),
                            properties: properties(r),
                            source_id: id(startNode(r)),
                            target_id: id(endNode(r))
                        }) as relationships
                        LIMIT $limit
                        """,
                        node_id=node_id,
                        limit=limit
                    )
                else:
                    # 获取指定深度的邻居
                    result = session.run(
                        """
                        MATCH path = (n)-[r*1..$depth]-(m)
                        WHERE id(n) = $node_id
                        WITH nodes(path) as nodes, relationships(path) as rels
                        UNWIND nodes as node
                        WITH DISTINCT node, rels
                        UNWIND rels as rel
                        WITH DISTINCT node, rel
                        LIMIT $limit
                        RETURN COLLECT(DISTINCT {
                            id: id(node),
                            labels: labels(node),
                            properties: properties(node)
                        }) as nodes,
                        COLLECT(DISTINCT {
                            id: id(rel),
                            type: type(rel),
                            properties: properties(rel),
                            source_id: id(startNode(rel)),
                            target_id: id(endNode(rel))
                        }) as relationships
                        """,
                        node_id=node_id,
                        depth=depth,
                        limit=limit
                    )

                graph_data = result.single()
                if not graph_data:
                    return {"nodes": [], "relationships": []}

                return {
                    "nodes": graph_data["nodes"],
                    "relationships": graph_data["relationships"]
                }

        except Neo4jError as e:
            logger.error(f"Neo4j neighbor query error: {str(e)}")
            raise Exception(f"获取节点邻居错误: {str(e)}")

    def search_knowledge_graph_by_field(self, field: str, value: str, limit: int = 100, case_sensitive: bool = False) -> Dict[str, Any]:
        """
        按字段值搜索知识图谱
        :param field: 要搜索的字段名称
        :param value: 字段的值
        :param limit: 限制返回的节点数量
        :param case_sensitive: 是否区分大小写
        :return: 包含匹配节点和相关关系的字典
        """
        try:
            with self.driver.session(database=self.target_database) as session:
                # 构建查询
                query = """
                    MATCH (n)
                    WHERE {where_clause}
                    RETURN DISTINCT
                        id(n) as id,
                        labels(n) as labels,
                        properties(n) as properties
                    LIMIT $limit
                """
                
                # 根据case_sensitive参数决定使用哪种匹配方式
                if case_sensitive:
                    where_clause = f"n.{field} = $value"
                else:
                    where_clause = f"toLower(toString(n.{field})) = toLower($value)"
                
                query = query.format(where_clause=where_clause)
                
                # 搜索匹配字段值的节点
                nodes_result = session.run(
                    query,
                    value=value,
                    limit=limit
                )

                nodes = []
                for record in nodes_result:
                    node = {
                        "id": record["id"],
                        "labels": record["labels"],
                        "properties": record["properties"]
                    }
                    nodes.append(node)
                logger.info(f"Found {len(nodes)} nodes with {field}={value}")

                if not nodes:
                    logger.warning(f"No nodes found with {field}={value}")
                    return {"nodes": [], "relationships": []}

                # 获取匹配节点之间的关系
                relationships_result = session.run(
                    """
                    MATCH (n)-[r]->(m)
                    WHERE id(n) IN $node_ids AND id(m) IN $node_ids
                    RETURN DISTINCT
                        id(r) as id,
                        type(r) as type,
                        properties(r) as properties,
                        id(startNode(r)) as source,
                        id(endNode(r)) as target
                    """,
                    node_ids=[node["id"] for node in nodes]
                )

                relationships = []
                for record in relationships_result:
                    relationship = {
                        "id": record["id"],
                        "type": record["properties"].get("type", record["type"]),
                        "source": record["source"],
                        "target": record["target"],
                        "properties": {k: v for k, v in record["properties"].items() if k != "type"}
                    }
                    relationships.append(relationship)
                logger.info(f"Found {len(relationships)} relationships between matching nodes")

                return {
                    "nodes": nodes,
                    "relationships": relationships
                }

        except Neo4jError as e:
            logger.error(f"Neo4j field search error: {str(e)}")
            raise Exception(f"Neo4j字段搜索错误: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in search_knowledge_graph_by_field: {str(e)}")
            raise

    def get_node_neighbors_by_name(self, name: str, depth: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        通过节点名称获取其邻居节点
        :param name: 节点的name属性值
        :param depth: 遍历深度
        :param limit: 限制返回的节点数量
        :return: 包含邻居节点和关系的字典
        """
        try:
            with self.driver.session(database=self.target_database) as session:
                # 首先找到目标节点
                result = session.run(
                    """
                    MATCH (n)
                    WHERE n.name = $name
                    RETURN id(n) as node_id
                    LIMIT 1
                    """,
                    name=name
                )
                record = result.single()
                if not record:
                    raise Exception(f"未找到名称为 '{name}' 的节点")
                
                return self.get_node_neighbors(record["node_id"], depth, limit)

        except Neo4jError as e:
            logger.error(f"Neo4j neighbor query error: {str(e)}")
            raise Exception(f"获取节点邻居错误: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in get_node_neighbors_by_name: {str(e)}")
            raise

    def get_node_neighbors_by_identifier(self, node_identifier: str, depth: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        通过节点标识符获取其邻居节点
        :param node_identifier: 节点的完整标识符（例如：4:2b1bc1df-df27-4e5a-be17-509b0d4f3578:11）
        :param depth: 遍历深度
        :param limit: 限制返回的节点数量
        :return: 包含邻居节点和关系的字典
        """
        try:
            with self.driver.session(database=self.target_database) as session:
                # 首先找到目标节点
                result = session.run(
                    """
                    MATCH (n)
                    WHERE n.entity_id = $node_identifier
                    RETURN id(n) as node_id
                    LIMIT 1
                    """,
                    node_identifier=node_identifier
                )
                record = result.single()
                if not record:
                    raise Exception(f"未找到标识符为 '{node_identifier}' 的节点")
                
                return self.get_node_neighbors(record["node_id"], depth, limit)

        except Neo4jError as e:
            logger.error(f"Neo4j neighbor query error: {str(e)}")
            raise Exception(f"获取节点邻居错误: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in get_node_neighbors_by_identifier: {str(e)}")
            raise

    def get_node_by_id(self, node_id: str) -> Optional[Dict]:
        """
        根据节点ID获取节点信息
        :param node_id: 节点ID
        :return: 节点信息字典，如果未找到则返回None
        """
        try:
            with self.driver.session(database=self.target_database) as session:
                result = session.run(
                    """
                    MATCH (n)
                    WHERE id(n) = $node_id
                    RETURN DISTINCT
                        id(n) as id,
                        labels(n) as labels,
                        properties(n) as properties
                    LIMIT 1
                    """,
                    node_id=int(node_id)
                )
                
                record = result.single()
                if record:
                    return {
                        "id": record["id"],
                        "labels": record["labels"],
                        "properties": record["properties"]
                    }
                return None

        except Neo4jError as e:
            logger.error(f"Neo4j get_node_by_id error: {str(e)}")
            raise Exception(f"获取节点信息错误: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in get_node_by_id: {str(e)}")
            raise

    def get_node_relationships(self, node_id: str, direction: str = "both") -> List[Dict]:
        """
        获取节点的关系
        :param node_id: 节点ID
        :param direction: 关系方向 ("in", "out", "both")
        :return: 关系列表
        """
        try:
            with self.driver.session(database=self.target_database) as session:
                # 根据方向构建查询
                if direction == "in":
                    query = """
                        MATCH (n)-[r]->(m)
                        WHERE id(m) = $node_id
                        RETURN DISTINCT
                            id(r) as id,
                            type(r) as type,
                            properties(r) as properties,
                            id(startNode(r)) as source,
                            id(endNode(r)) as target
                    """
                elif direction == "out":
                    query = """
                        MATCH (n)-[r]->(m)
                        WHERE id(n) = $node_id
                        RETURN DISTINCT
                            id(r) as id,
                            type(r) as type,
                            properties(r) as properties,
                            id(startNode(r)) as source,
                            id(endNode(r)) as target
                    """
                else:  # both
                    query = """
                        MATCH (n)-[r]-(m)
                        WHERE id(n) = $node_id OR id(m) = $node_id
                        RETURN DISTINCT
                            id(r) as id,
                            type(r) as type,
                            properties(r) as properties,
                            id(startNode(r)) as source,
                            id(endNode(r)) as target
                    """
                
                result = session.run(query, node_id=int(node_id))
                
                relationships = []
                for record in result:
                    relationship = {
                        "id": record["id"],
                        "type": record["properties"].get("type", record["type"]),
                        "source": record["source"],
                        "target": record["target"],
                        "properties": {k: v for k, v in record["properties"].items() if k != "type"}
                    }
                    relationships.append(relationship)
                
                return relationships

        except Neo4jError as e:
            logger.error(f"Neo4j get_node_relationships error: {str(e)}")
            raise Exception(f"获取节点关系错误: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in get_node_relationships: {str(e)}")
            raise
