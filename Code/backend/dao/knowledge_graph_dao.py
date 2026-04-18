from typing import Dict, Optional, List
from repository.knowledge_graph_repository import KnowledgeGraphRepository

class KnowledgeGraphDAO:
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        """
        初始化KnowledgeGraphDAO
        :param neo4j_uri: Neo4j数据库URI
        :param neo4j_user: Neo4j用户名
        :param neo4j_password: Neo4j密码
        """
        self.repository = KnowledgeGraphRepository(
            uri=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password
        )

    def get_knowledge_graph(self, course_name: str, limit: int = 100) -> Dict:
        """
        获取指定课程的知识图谱数据
        :param course_name: 课程名
        :param limit: 限制返回的节点数量
        :return: 知识图谱数据
        """
        return self.repository.get_knowledge_graph(course_name=course_name, limit=limit)

    def search_knowledge_graph(self, keyword: str, limit: int = 100, case_sensitive: bool = False) -> Dict:
        """
        搜索知识图谱
        :param keyword: 搜索关键词
        :param limit: 限制返回的节点数量
        :param case_sensitive: 是否区分大小写
        :return: 搜索结果
        """
        return self.repository.search_knowledge_graph(
            keyword=keyword,
            limit=limit,
            case_sensitive=case_sensitive
        )

    def get_node_neighbors(self, node_id: int, depth: int = 1, limit: int = 50) -> Dict:
        """
        获取节点的邻居节点
        :param node_id: 节点ID
        :param depth: 遍历深度
        :param limit: 限制返回的节点数量
        :return: 邻居节点数据
        """
        return self.repository.get_node_neighbors(node_id=node_id, depth=depth, limit=limit)

    def search_knowledge_graph_by_field(self, field: str, value: str, limit: int = 100, case_sensitive: bool = False) -> Dict:
        """
        按字段值搜索知识图谱
        :param field: 要搜索的字段名称
        :param value: 字段的值
        :param limit: 限制返回的节点数量
        :param case_sensitive: 是否区分大小写
        :return: 搜索结果
        """
        return self.repository.search_knowledge_graph_by_field(
            field=field,
            value=value,
            limit=limit,
            case_sensitive=case_sensitive
        )

    def get_node_neighbors_by_name(self, name: str, depth: int = 1, limit: int = 50) -> Dict:
        """
        通过节点名称获取其邻居节点
        :param name: 节点的name属性值
        :param depth: 遍历深度
        :param limit: 限制返回的节点数量
        :return: 邻居节点数据
        """
        return self.repository.get_node_neighbors_by_name(
            name=name,
            depth=depth,
            limit=limit
        )

    def get_node_neighbors_by_identifier(self, node_identifier: str, depth: int = 1, limit: int = 50) -> Dict:
        """
        通过节点标识符获取其邻居节点
        :param node_identifier: 节点的完整标识符
        :param depth: 遍历深度
        :param limit: 限制返回的节点数量
        :return: 邻居节点数据
        """
        return self.repository.get_node_neighbors_by_identifier(
            node_identifier=node_identifier,
            depth=depth,
            limit=limit
        )

    def get_node_by_id(self, node_id: str) -> Optional[Dict]:
        """
        根据节点ID获取节点信息
        :param node_id: 节点ID
        :return: 节点信息字典，如果未找到则返回None
        """
        return self.repository.get_node_by_id(node_id)

    def get_node_relationships(self, node_id: str, direction: str = "both") -> List[Dict]:
        """
        获取节点的关系
        :param node_id: 节点ID
        :param direction: 关系方向 ("in", "out", "both")
        :return: 关系列表
        """
        return self.repository.get_node_relationships(node_id, direction)

    def close(self):
        """
        关闭数据库连接
        """
        self.repository.close()

    def add_node(self, node: dict):
        """
        向 Neo4j 插入一个节点，支持 node['labels'] 作为标签，node['properties'] 作为属性
        """
        labels = ":".join(node.get("labels", ["CourseRoot"]))
        properties = node.get("properties", {})
        # 构造 Cypher 属性字符串
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        cypher = f"CREATE (n:{labels} {{{props_str}}})"
        with self.repository.driver.session() as session:
            session.run(
                cypher,
                **properties
            )

    def delete_nodes_by_filename(self, filename: str, course_name: str):
        return self.repository.delete_nodes_by_filename(filename, course_name)