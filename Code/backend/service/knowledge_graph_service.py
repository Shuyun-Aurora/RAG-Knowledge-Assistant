from dao.knowledge_graph_dao import KnowledgeGraphDAO
from dao.vector_dao import VectorDAO
from typing import List, Dict, Any
import logging

class KnowledgeGraphService:
    """知识图谱服务，用于智能问答时检索相关知识节点"""
    
    def __init__(self, knowledge_graph_dao: KnowledgeGraphDAO, vector_dao: VectorDAO):
        self.knowledge_graph_dao = knowledge_graph_dao
        self.vector_dao = vector_dao
        self.logger = logging.getLogger(__name__)

    def get_knowledge_graph(self, course_name: str, limit: int = 100) -> Dict:
        """
        获取指定课程的知识图谱数据
        :param course_name: 课程名
        :param limit: 限制返回的节点数量
        :return: 知识图谱数据
        """
        return self.knowledge_graph_dao.get_knowledge_graph(course_name=course_name, limit=limit)

    def search_knowledge_graph(self, keyword: str, limit: int = 100, case_sensitive: bool = False) -> Dict:
        """
        搜索知识图谱
        :param keyword: 搜索关键词
        :param limit: 限制返回的节点数量
        :param case_sensitive: 是否区分大小写
        :return: 搜索结果
        """
        try:
            return self.knowledge_graph_dao.search_knowledge_graph(
                keyword=keyword,
                limit=limit,
                case_sensitive=case_sensitive
            )
        except Exception as e:
            raise Exception(f"搜索知识图谱失败: {str(e)}")

    def get_node_neighbors(self, node_id: int, depth: int = 1, limit: int = 50) -> Dict:
        """
        获取节点的邻居节点
        :param node_id: 节点ID
        :param depth: 遍历深度
        :param limit: 限制返回的节点数量
        :return: 邻居节点数据
        """
        try:
            return self.knowledge_graph_dao.get_node_neighbors(
                node_id=node_id,
                depth=depth,
                limit=limit
            )
        except Exception as e:
            raise Exception(f"获取节点邻居失败: {str(e)}")

    def close(self):
        """
        关闭数据库连接
        """
        try:
            self.knowledge_graph_dao.close()
        except Exception as e:
            raise Exception(f"关闭知识图谱连接失败: {str(e)}")

    def search_knowledge_graph_by_field(self, field: str, value: str, limit: int = 100, case_sensitive: bool = False) -> Dict:
        """
        按字段值搜索知识图谱
        :param field: 要搜索的字段名称
        :param value: 字段的值
        :param limit: 限制返回的节点数量
        :param case_sensitive: 是否区分大小写
        :return: 搜索结果
        """
        try:
            return self.knowledge_graph_dao.search_knowledge_graph_by_field(
                field=field,
                value=value,
                limit=limit,
                case_sensitive=case_sensitive
            )
        except Exception as e:
            raise Exception(f"按字段搜索知识图谱失败: {str(e)}")

    async def search_related_nodes(
        self, 
        query: str, 
        course_name: str, 
        top_k: int = 5,
        include_neighbors: bool = True,
        neighbor_depth: int = 1,
        similarity_threshold: float = 0.4
    ) -> Dict[str, Any]:
        """
        高精度向量检索 + 图结构扩展的混合搜索
        """
        try:
            from repository.embedding_repository import QwenEmbeddings
            from config.settings import settings
            from dao.vector_dao import VectorDAO
            embedding = QwenEmbeddings(settings.DASHSCOPE_API_KEY)
            kg_vector_dao = VectorDAO(embedding, collection_name="kg_collection")
            self.logger.info(f"开始高精度知识图谱搜索，查询: {query[:100]}...")
            self.logger.info(f"相似度阈值: {similarity_threshold}")
            related_nodes = await self._high_precision_vector_search(
                query, course_name, top_k, similarity_threshold, kg_vector_dao
            )
            if not related_nodes:
                self.logger.warning("未找到相似度足够高的相关节点")
                return {"nodes": [], "edges": [], "context": "", "search_info": "相似度阈值过高"}
            self.logger.info(f"向量检索找到 {len(related_nodes)} 个高相似度节点")
            node_details = await self._get_node_details([node["id"] for node in related_nodes])
            all_nodes = node_details
            all_edges = []
            if include_neighbors:
                neighbor_nodes, neighbor_edges = await self._get_neighbor_nodes(
                    [node["id"] for node in node_details], 
                    neighbor_depth
                )
                all_nodes.extend(neighbor_nodes)
                all_edges.extend(neighbor_edges)
                self.logger.info(f"图结构扩展后，总节点数: {len(all_nodes)}, 总边数: {len(all_edges)}")
            context = self._build_enhanced_context(all_nodes, all_edges, related_nodes)
            result = {
                "nodes": all_nodes,
                "edges": all_edges,
                "context": context,
                "related_count": len(related_nodes),
                "total_nodes": len(all_nodes),
                "total_edges": len(all_edges),
                "search_info": f"向量检索{len(related_nodes)}个节点，图扩展后{len(all_nodes)}个节点"
            }
            self.logger.info(f"知识图谱搜索完成，找到 {len(all_nodes)} 个节点，{len(all_edges)} 个边")
            return result
        except Exception as e:
            self.logger.error(f"知识图谱搜索失败: {e}")
            return {"nodes": [], "edges": [], "context": "", "error": str(e)}

    async def _high_precision_vector_search(
        self, 
        query: str, 
        course_name: str, 
        top_k: int, 
        similarity_threshold: float,
        kg_vector_dao=None
    ) -> List[Dict[str, Any]]:
        """
        高精度向量检索，只返回相似度高于阈值的节点
        """
        try:
            if kg_vector_dao is None:
                from repository.embedding_repository import QwenEmbeddings
                from config.settings import settings
                from dao.vector_dao import VectorDAO
                embedding = QwenEmbeddings(settings.DASHSCOPE_API_KEY)
                kg_vector_dao = VectorDAO(embedding, collection_name="kg_collection")
            search_results = kg_vector_dao.search(
                query=query,
                k=top_k * 3,  # 获取更多候选结果
                course_name=course_name
            )
            self.logger.info(f"向量搜索返回 {len(search_results)} 个候选结果")
            filtered_results = []
            all_kg_nodes = []
            for doc, score in search_results:
                self.logger.info(f"候选结果: type={doc.metadata.get('type', 'None')}, "
                               f"name={doc.metadata.get('node_name', doc.metadata.get('filename', 'Unknown'))}, "
                               f"distance={score:.3f}")
                if doc.metadata.get("type") == "knowledge_graph_node":
                    similarity = 1.0 - score
                    node_info = {
                        "id": doc.metadata.get("node_id"),
                        "name": doc.metadata.get("node_name", "Unknown"),
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": similarity,
                        "distance": score
                    }
                    all_kg_nodes.append(node_info)
                    if similarity >= similarity_threshold:
                        filtered_results.append(node_info)
            filtered_results.sort(key=lambda x: x["similarity"], reverse=True)
            all_kg_nodes.sort(key=lambda x: x["similarity"], reverse=True)
            result = filtered_results[:top_k]
            self.logger.info(f"找到 {len(all_kg_nodes)} 个知识图谱节点")
            if all_kg_nodes:
                self.logger.info(f"所有知识图谱节点相似度分布:")
                for i, node in enumerate(all_kg_nodes[:5]):
                    self.logger.info(f"  {i+1}. {node['name']}: 相似度={node['similarity']:.3f}, 距离={node['distance']:.3f}")
                if len(all_kg_nodes) > 5:
                    self.logger.info(f"  ... 还有 {len(all_kg_nodes) - 5} 个节点")
            self.logger.info(f"阈值过滤后: 找到 {len(result)} 个节点（阈值: {similarity_threshold}）")
            if result:
                self.logger.info(f"最终结果相似度范围: {min([r['similarity'] for r in result]):.3f} - {max([r['similarity'] for r in result]):.3f}")
            else:
                self.logger.info(f"没有节点达到阈值 {similarity_threshold}")
            return result
        except Exception as e:
            self.logger.error(f"高精度向量搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def _vector_search_nodes(self, query: str, course_name: str, top_k: int) -> List[Dict[str, Any]]:
        """使用向量检索找到相关节点（兼容旧版本）"""
        return await self._high_precision_vector_search(query, course_name, top_k, 0.0)
    
    async def _get_node_details(self, node_ids: List[str]) -> List[Dict[str, Any]]:
        """获取节点的详细信息"""
        try:
            details = []
            for node_id in node_ids:
                node_info = self.knowledge_graph_dao.get_node_by_id(node_id)
                if node_info:
                    details.append(node_info)
            return details
        except Exception as e:
            self.logger.error(f"获取节点详情失败: {e}")
            return []
    
    async def _get_neighbor_nodes(self, node_ids: List[str], depth: int = 1) -> tuple[List[Dict], List[Dict]]:
        """获取相邻节点和边"""
        try:
            neighbors = []
            edges = []
            
            for node_id in node_ids:
                # 使用dao层的get_node_neighbors方法
                neighbor_result = self.knowledge_graph_dao.get_node_neighbors(
                    node_id=int(node_id),  # 确保node_id是整数
                    depth=depth,
                    limit=50
                )
                
                # 提取节点和关系
                if neighbor_result.get("nodes"):
                    neighbors.extend(neighbor_result["nodes"])
                if neighbor_result.get("relationships"):
                    edges.extend(neighbor_result["relationships"])
            
            # 去重
            unique_neighbors = []
            seen_neighbor_ids = set()
            for neighbor in neighbors:
                neighbor_id = neighbor.get("id")
                if neighbor_id not in seen_neighbor_ids:
                    unique_neighbors.append(neighbor)
                    seen_neighbor_ids.add(neighbor_id)
            
            unique_edges = []
            seen_edge_ids = set()
            for edge in edges:
                edge_id = edge.get("id")
                if edge_id not in seen_edge_ids:
                    unique_edges.append(edge)
                    seen_edge_ids.add(edge_id)
            
            return unique_neighbors, unique_edges
        except Exception as e:
            self.logger.error(f"获取相邻节点失败: {e}")
            return [], []
    
    def _build_enhanced_context(
        self, 
        nodes: List[Dict], 
        edges: List[Dict], 
        related_nodes: List[Dict]
    ) -> str:
        """
        构建增强的上下文信息，区分核心节点和扩展节点
        
        Args:
            nodes: 所有节点（包括核心节点和扩展节点）
            edges: 所有边关系
            related_nodes: 向量检索找到的核心节点
            
        Returns:
            增强的上下文字符串
        """
        try:
            context_parts = []
            
            # 获取核心节点ID集合
            core_node_ids = {node["id"] for node in related_nodes}
            
            # 分离核心节点和扩展节点
            core_nodes = [node for node in nodes if node.get("id") in core_node_ids]
            extended_nodes = [node for node in nodes if node.get("id") not in core_node_ids]
            
            # 辅助函数：安全获取节点字段
            def get_node_field(node, field_name, default=""):
                """安全获取节点字段，处理不同数据结构"""
                # 尝试多种可能的字段名
                possible_fields = [field_name]
                if field_name == 'name':
                    possible_fields = ['name', 'node_name', 'properties.name', 'metadata.node_name']
                elif field_name == 'type':
                    possible_fields = ['type', 'entity_type', 'node_type', 'metadata.node_type', 'labels', 'properties.type', 'properties.entity_type']
                elif field_name == 'description':
                    possible_fields = ['description', 'metadata.description', 'properties.description']
                elif field_name == 'content':
                    possible_fields = ['content', 'metadata.content', 'properties.content']
                
                for field in possible_fields:
                    if '.' in field:
                        # 处理嵌套字段，如 properties.name, metadata.node_name
                        parts = field.split('.')
                        value = node
                        for part in parts:
                            if isinstance(value, dict) and part in value:
                                value = value[part]
                            else:
                                value = None
                                break
                        if value and str(value).strip():
                            return str(value).strip()
                    else:
                        # 直接字段
                        value = node.get(field)
                        if value and str(value).strip():
                            return str(value).strip()
                
                return default
            
            context_parts.append("## 核心相关知识节点（高相似度匹配）:")
            for node in core_nodes:
                # 找到对应的相似度信息
                similarity_info = next((r for r in related_nodes if r["id"] == node.get("id")), None)
                similarity_str = f" (相似度: {similarity_info['similarity']:.3f})" if similarity_info else ""
                
                node_name = get_node_field(node, 'name')
                node_type = get_node_field(node, 'type')
                if isinstance(node_type, list):
                    node_type = ', '.join(str(t) for t in node_type if t) if node_type else ''
                elif not node_type:
                    node_type = ''
                node_desc = get_node_field(node, 'description', '暂无描述')
                node_content = get_node_field(node, 'content', '暂无内容')
                
                context_parts.append(f"### {node_name}{similarity_str}")
                context_parts.append(f"**类型**: {node_type}")
                context_parts.append(f"**描述**: {node_desc}")
                context_parts.append(f"**内容**: {node_content}")

                # 处理重要性字段
                importance = get_node_field(node, 'importance')
                if importance and importance != "未知":
                    context_parts.append(f"**重要性**: {importance}")
                context_parts.append("")
            
            # 如果有扩展节点，添加扩展节点信息
            if extended_nodes:
                context_parts.append("## 相关知识扩展节点（图结构扩展）:")
                for node in extended_nodes:
                    node_name = get_node_field(node, 'name')
                    node_type = get_node_field(node, 'type')
                    if isinstance(node_type, list):
                        node_type = ', '.join(str(t) for t in node_type if t) if node_type else ''
                    elif not node_type:
                        node_type = ''
                    node_desc = get_node_field(node, 'description', '暂无描述')
                    node_content = get_node_field(node, 'content', '暂无内容')
                    
                    context_parts.append(f"### {node_name}")
                    context_parts.append(f"**类型**: {node_type}")
                    context_parts.append(f"**描述**: {node_desc}")
                    context_parts.append(f"**内容**: {node_content}")

                    # 处理重要性字段
                    importance = get_node_field(node, 'importance')
                    if importance and importance != "未知":
                        context_parts.append(f"**重要性**: {importance}")
                    context_parts.append("")
            
            # 添加关系信息
            if edges:
                context_parts.append("## 节点关系网络:")
                for edge in edges:
                    # 查找源节点和目标节点（支持多种ID类型匹配）
                    source_id = edge.get('source_id')
                    target_id = edge.get('target_id')
                    
                    def find_node_by_id(nodes_list, node_id):
                        """通过ID查找节点，支持多种ID类型"""
                        if node_id is None:
                            return None
                        
                        # 尝试多种匹配方式
                        for node in nodes_list:
                            node_id_val = node.get('id')
                            if node_id_val is not None:
                                # 精确匹配
                                if node_id_val == node_id:
                                    return node
                                # 字符串匹配
                                if str(node_id_val) == str(node_id):
                                    return node
                                # 整数匹配
                                try:
                                    if int(node_id_val) == int(node_id):
                                        return node
                                except (ValueError, TypeError):
                                    pass
                        return None
                    
                    source_node = find_node_by_id(nodes, source_id)
                    target_node = find_node_by_id(nodes, target_id)
                    
                    # 如果找不到节点，显示ID以便调试
                    source_name = get_node_field(source_node, 'name') if source_node else f"未知节点({source_id})"
                    target_name = get_node_field(target_node, 'name') if target_node else f"未知节点({target_id})"
                    relation_type = edge.get('type', '未知关系')
                    description = edge.get('properties', {}).get('description', '')
                    
                    # 标记核心节点（也需要支持多种ID类型）
                    def is_core_node(node_id, core_ids):
                        """检查是否为核心节点，支持多种ID类型"""
                        if node_id is None:
                            return False
                        for core_id in core_ids:
                            if core_id == node_id or str(core_id) == str(node_id):
                                try:
                                    if int(core_id) == int(node_id):
                                        return True
                                except (ValueError, TypeError):
                                    pass
                        return False
                    
                    source_marker = "⭐" if is_core_node(source_id, core_node_ids) else ""
                    target_marker = "⭐" if is_core_node(target_id, core_node_ids) else ""
                    
                    context_parts.append(f"- **{source_name}{source_marker}** --[{relation_type}]--> **{target_name}{target_marker}**: {description}")
                context_parts.append("")
            
            context_parts.append("## 搜索策略说明:")
            context_parts.append("1. **高精度向量检索**: 通过语义相似度找到最相关的核心节点")
            context_parts.append("2. **图结构扩展**: 获取核心节点的邻居节点，构建完整的知识网络")
            context_parts.append("3. **关系分析**: 利用节点间的关系进行深度推理")
            context_parts.append("")
            context_parts.append("## 关系类型说明:")
            context_parts.append("- **CONTAINS** ⭐: 包含关系（算法包含具体规则）")
            context_parts.append("- **FOLLOWS** ➡️: 顺序关系（执行顺序）")
            context_parts.append("- **RELATES_TO** 🔗: 相关关系（概念关联）")
            context_parts.append("- **DEFINES** 📝: 定义关系（概念定义公式）")
            context_parts.append("")
            context_parts.append("请基于以上结构化知识网络，提供准确、详细、有逻辑的回答。")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            self.logger.error(f"构建增强上下文失败: {e}")
            return "知识图谱信息构建失败"

    def _build_context(self, nodes: List[Dict], edges: List[Dict]) -> str:
        """构建上下文信息（兼容旧版本）"""
        return self._build_enhanced_context(nodes, edges, [])

    def delete_nodes_by_filename(self, filename: str, course_name: str) -> Dict[str, Any]:
        """
        根据文件名删除知识图谱中的相关节点及其所有子节点
        
        :param filename: 文件名
        :param course_name: 课程名
        :return: 删除结果
        """
        try:
            return self.knowledge_graph_dao.delete_nodes_by_filename(filename, course_name)
        except Exception as e:
            raise Exception(f"删除知识图谱节点失败: {str(e)}")

    def delete_kg_vectors_by_filename(self, filename: str, course_name: str) -> Dict[str, Any]:
        """
        删除kg_collection中与指定文件名相关的向量
        
        :param filename: 文件名
        :param course_name: 课程名
        :return: 删除结果
        """
        try:
            from repository.embedding_repository import QwenEmbeddings
            from config.settings import settings
            from dao.vector_dao import VectorDAO
            
            embedding = QwenEmbeddings(settings.DASHSCOPE_API_KEY)
            kg_vector_dao = VectorDAO(embedding, collection_name="kg_collection")
            
            # 删除与文件名相关的向量
            deleted_count = kg_vector_dao.delete_by_source(filename)
            
            # 删除与课程相关的知识图谱向量（但保留CourseRoot节点）
            # 由于向量存储的限制，我们只能通过source字段来删除
            # 对于FileRoot节点，source是文件名；对于其他节点，source是课程名
            course_deleted_count = 0
            
            # 尝试删除可能存在的课程相关向量（但保留CourseRoot）
            try:
                # 获取所有课程相关的向量
                all_docs = kg_vector_dao._get_all_documents()
                course_related_ids = []
                
                for i, metadata in enumerate(all_docs.get('metadatas', [])):
                    if (metadata.get('course') == course_name and 
                        metadata.get('source') == f"knowledge_graph_{course_name}" and
                        metadata.get('node_type') != 'CourseRoot'):
                        # 只删除非CourseRoot的课程相关节点
                        doc_id = all_docs.get('ids', [])[i] if i < len(all_docs.get('ids', [])) else None
                        if doc_id:
                            course_related_ids.append(doc_id)
                
                if course_related_ids:
                    # 由于VectorDAO没有delete方法，我们只能通过delete_by_source来删除
                    # 这里我们删除所有课程相关的向量，然后在重新存储时保留CourseRoot
                    course_deleted_count = kg_vector_dao.delete_by_source(f"knowledge_graph_{course_name}")
                    
                    # 重新存储CourseRoot节点
                    if self.knowledge_graph_dao:
                        try:
                            # 获取CourseRoot节点
                            course_root_data = self.knowledge_graph_dao.get_knowledge_graph(course_name=course_name, limit=1)
                            if course_root_data and course_root_data.get("nodes"):
                                for node in course_root_data["nodes"]:
                                    if node.get("labels") and "CourseRoot" in node["labels"]:
                                        # 重新存储CourseRoot节点到向量数据库
                                        props = node.get("properties", {})
                                        name = props.get("name", "")
                                        desc = props.get("description", "")
                                        content = props.get("content", "")
                                        node_content = f"{name} - {desc} {content}"
                                        
                                        metadata = {
                                            "type": "knowledge_graph_node",
                                            "node_id": str(node.get("id")),
                                            "node_name": name,
                                            "node_type": "CourseRoot",
                                            "course": course_name,
                                            "source": f"knowledge_graph_{course_name}",
                                            "filename": f"knowledge_graph_{course_name}",
                                            "description": desc,
                                            "content": content,
                                            "importance": props.get("importance", ""),
                                            "category": "CourseRoot"
                                        }
                                        
                                        kg_vector_dao.add([node_content], [metadata])
                                        kg_vector_dao.save()
                                        self.logger.info("重新存储了CourseRoot节点到向量数据库")
                                        break
                        except Exception as e:
                            self.logger.warning(f"重新存储CourseRoot节点时出错: {e}")
                    
            except Exception as e:
                self.logger.warning(f"删除课程相关向量时出错: {e}")
            
            total_deleted = deleted_count + course_deleted_count
            
            return {
                "success": True,
                "message": f"成功删除文件名 '{filename}' 相关的知识图谱向量",
                "deleted_vectors": total_deleted,
                "filename_deleted": deleted_count,
                "course_deleted": course_deleted_count
            }
        except Exception as e:
            self.logger.error(f"删除知识图谱向量失败: {e}")
            return {"success": False, "message": f"删除知识图谱向量失败: {str(e)}", "deleted_vectors": 0}

    def add_node(self, node: dict):
        """
        调用 DAO 层插入知识图谱节点
        """
        return self.knowledge_graph_dao.add_node(node)

    def ensure_course_root(self, course_name: str) -> Dict:
        return self.knowledge_graph_dao.ensure_course_root(course_name)

    def ensure_course_root_and_link_file_root(self, course_name: str, filename: str) -> Dict:
        return self.knowledge_graph_dao.ensure_course_root_and_link_file_root(course_name, filename)
