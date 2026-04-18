import os
import sys
import json
import logging
from openai import OpenAI
import requests
from typing import List, Dict, Any, Optional
from neo4j import AsyncGraphDatabase
import networkx as nx

# 调整路径以指向 app/lib 目录
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)  # 回到 app 目录
lib_path = os.path.join(app_dir, 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

try:
    from lib.lightrag.types import KnowledgeGraph as Graph, KnowledgeGraphNode as Node, KnowledgeGraphEdge as Edge
    from lib.lightrag.kg.neo4j_impl import Neo4JStorage
except ImportError as e:
    print(f"Failed to import from lightrag. Please ensure the structure is correct.")
    print(f"Attempted to add '{lib_path}' to sys.path.")
    print(f"Current sys.path: {sys.path}")
    raise e

class LightRAGKnowledgeGraph:
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_pass: str, deepseek_key: str):
        """
        初始化知识图谱系统
        
        Args:
            neo4j_uri: Neo4j数据库URI
            neo4j_user: Neo4j用户名
            neo4j_pass: Neo4j密码
            deepseek_key: DeepSeek API密钥
        """
        # 设置日志
        self.logger = logging.getLogger("KnowledgeGraph")
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # 设置环境变量（LightRAG需要）
        os.environ["NEO4J_URI"] = neo4j_uri
        os.environ["NEO4J_USERNAME"] = neo4j_user
        os.environ["NEO4J_PASSWORD"] = neo4j_pass

        # 初始化Neo4j驱动和LightRAG存储
        self.driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
        self.graph_store = Neo4JStorage(namespace="neo4j", global_config=None, embedding_func=None)
        
        # 初始化DeepSeek API配置
        self.deepseek_key = deepseek_key
        self.deepseek_base_url = "https://api.deepseek.com/v1"
        
        self.logger.info("LightRAG Knowledge Graph system initialized.")

    async def async_init(self):
        """异步初始化图谱存储"""
        try:
            self.logger.info("开始初始化图谱存储...")
            await self.graph_store.initialize()
            self.logger.info("图谱存储初始化完成")
        except Exception as e:
            self.logger.error(f"初始化图谱存储失败: {e}")
            raise

    async def close(self):
        """关闭所有连接"""
        if self.driver:
            await self.driver.close()
        if self.graph_store:
            await self.graph_store.finalize()
        self.logger.info("All connections closed.")

    async def clear_database(self):
        """清空数据库中的所有节点和关系"""
        try:
            async with self.driver.session() as session:
                await session.run("MATCH (n) DETACH DELETE n")
            self.logger.info("Database cleared successfully.")
        except Exception as e:
            self.logger.error(f"Error clearing database: {e}")
            raise

    async def test_connection(self):
        """测试Neo4j连接"""
        try:
            self.logger.info("测试Neo4j连接...")
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                if record and record["test"] == 1:
                    self.logger.info("Neo4j连接正常")
                    return True
                else:
                    self.logger.error("Neo4j连接测试失败")
                    return False
        except Exception as e:
            self.logger.error(f"Neo4j连接测试失败: {e}")
            return False

    def _extract_graph_from_text(self, text: str, course_name: str, filename: str = None) -> Graph:
        """
        使用LLM从文本中提取实体和关系（本次只针对单个文件内容生成知识子图）

        Args:
            text: 输入文本
            course_name: 课程名称
            filename: 文件名（用于子图标识）

        Returns:
            Graph: 包含节点和边的图结构
        """
        prompt = f"""
        请从以下文本中提取详细的知识图谱，要求：
        
        **重要：必须生成严格的树状结构，绝对禁止环状关系！**
        - 每个节点最多只能有一个父节点
        - 关系必须是单向的，不能形成循环
        - 结构应该像文件夹一样可以层层展开

        1. **节点提取**（必须包含以下类型）：
        - **Concept**：核心概念、定义、理论
        - **Formula**：数学公式、表达式
        - **Algorithm**：算法、方法
        - **Process**：操作流程、步骤
        - **Example**：示例、案例

        每个节点必须包含：
        ```json
        {{
        "id": "唯一标识（小写+下划线）",
        "type": "Concept/Formula/Algorithm/Process/Example",
        "properties": {{
            "name": "显示名称",
            "course": "{course_name}",
            "description": "详细解释",
            "content": "具体内容（如公式、步骤、定义等）",
            "importance": "重要性（High/Medium/Low）",
            "category": "分类标签"
        }}
        }}
        ```

        2. **关系提取**（必须包含以下类型）：
        - `CONTAINS`：包含关系（A包含B，如算法包含具体规则）
        - `FOLLOWS`：顺序关系（A在B之后执行）
        - `RELATES_TO`：相关关系（A与B相关）
        - `DEFINES`：定义关系（概念定义公式）

        关系格式：
        ```json
        {{
        "source_id": "来源节点ID",
        "target_id": "目标节点ID",
        "type": "关系类型",
        "properties": {{
            "description": "关系的详细描述",
            "strength": "关系强度（Strong/Medium/Weak）",
            "direction": "关系方向（Forward）"
        }}
        }}
        ```

        3. **特殊要求**：
        - 对于数学公式，必须提取完整的公式内容
        - 对于算法规则，必须提取具体的规则名称和内容
        - 对于概念，必须提取完整的定义和解释
        - **严格创建树状结构，绝对禁止环**：
          * 算法与规则之间用 `CONTAINS` 关系连接（算法包含具体规则，适用于并行规则）
          * 算法规则之间用 `FOLLOWS` 关系连接（规则1 FOLLOWS 规则2，适用于严格顺序规则）
          * **重要：CONTAINS 和 FOLLOWS 不能同时使用，避免环**
          * 概念与公式之间用 `DEFINES` 关系连接
          * 相关概念之间用 `RELATES_TO` 关系连接
        - 每个节点最多只能有1个父节点关系（被包含、被定义、被相关）
        - 优先提取具有教学价值的知识点
        - **确保关系是单向的，便于展开和教学**
        - **关系必须形成有向无环图（DAG）**

        文本内容：
        ---
        {text[:10000]}
        ---

        请返回完整的JSON格式，包含所有提取的节点和关系。
        
        **重要：必须包含边关系！** 如果文本中有相关概念，必须创建它们之间的连接关系。
        
        **绝对禁止创建环状关系！** 确保每个节点最多只有一个父节点，关系必须是单向的树状结构。
        
        示例JSON格式（展示两种关系使用方式）：
        
        **方式1：并行规则使用CONTAINS**
        ```json
        {{
          "nodes": [
            {{
              "id": "dpll_algorithm",
              "type": "Algorithm",
              "properties": {{
                "name": "DPLL算法",
                "course": "{course_name}",
                "description": "Davis-Putnam-Logemann-Loveland算法",
                "content": "基于回溯搜索的SAT求解算法",
                "importance": "High",
                "category": "SAT求解"
              }}
            }},
            {{
              "id": "decide_rule",
              "type": "Process",
              "properties": {{
                "name": "Decide Rule",
                "course": "{course_name}",
                "description": "选择未赋值的变量并赋值",
                "content": "选择一个未赋值的变量，给它赋值为true或false",
                "importance": "High",
                "category": "DPLL规则"
              }}
            }},
            {{
              "id": "unit_propagate_rule",
              "type": "Process",
              "properties": {{
                "name": "Unit Propagate Rule",
                "course": "{course_name}",
                "description": "对单位子句进行传播",
                "content": "如果存在单位子句，则强制赋值使其为真",
                "importance": "High",
                "category": "DPLL规则"
              }}
            }}
          ],
          "edges": [
            {{
              "source_id": "dpll_algorithm",
              "target_id": "decide_rule",
              "type": "CONTAINS",
              "properties": {{
                "description": "DPLL算法包含Decide规则",
                "strength": "Strong",
                "direction": "Forward",
              }}
            }},
            {{
              "source_id": "dpll_algorithm",
              "target_id": "unit_propagate_rule",
              "type": "CONTAINS",
              "properties": {{
                "description": "DPLL算法包含Unit Propagate规则",
                "strength": "Strong",
                "direction": "Forward",
                "context": "算法组成"
              }}
            }}
          ]
        }}
        ```
        
        **方式2：顺序规则使用FOLLOWS**
        ```json
        {{
          "nodes": [
            {{
              "id": "sorting_algorithm",
              "type": "Algorithm",
              "properties": {{
                "name": "快速排序",
                "course": "{course_name}",
                "description": "分治排序算法",
                "content": "选择基准元素，分区排序",
                "difficulty": "Intermediate",
                "importance": "High",
                "category": "排序算法"
              }}
            }},
            {{
              "id": "step1_choose_pivot",
              "type": "Process",
              "properties": {{
                "name": "选择基准元素",
                "course": "{course_name}",
                "description": "选择数组中的一个元素作为基准",
                "content": "通常选择最后一个元素作为基准",
                "difficulty": "Beginner",
                "importance": "High",
                "category": "快速排序步骤"
              }}
            }},
            {{
              "id": "step2_partition",
              "type": "Process",
              "properties": {{
                "name": "分区操作",
                "course": "{course_name}",
                "description": "根据基准元素进行分区",
                "content": "将小于基准的元素放在左边，大于基准的元素放在右边",
                "difficulty": "Intermediate",
                "importance": "High",
                "category": "快速排序步骤"
              }}
            }}
          ],
          "edges": [
            {{
              "source_id": "step1_choose_pivot",
              "target_id": "step2_partition",
              "type": "FOLLOWS",
              "properties": {{
                "description": "选择基准元素后执行分区操作",
                "strength": "Strong",
                "direction": "Forward",
                "context": "执行顺序"
              }}
            }}
          ]
        }}
        ```
        
        注意：两种方式都避免了环，形成了严格的树状结构。
        
        JSON Output:
        """

        try:
            self.logger.info("准备调用DeepSeek API...")
            # 使用requests直接调用DeepSeek API
            headers = {
                "Authorization": f"Bearer {self.deepseek_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2, # 稍微提高温度以获取更丰富的输出
                "max_tokens": 8000, # 使用API支持的最大值
                "response_format": {"type": "json_object"}
            }

            self.logger.info(f"发送请求到DeepSeek API，文本长度: {len(text)} 字符")
            self.logger.info(f"API URL: {self.deepseek_base_url}/chat/completions")
            self.logger.info(f"请求数据大小: {len(str(data))} 字符")
            
            try:
                self.logger.info("开始发送HTTP请求...")
                response = requests.post(
                    f"{self.deepseek_base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=240  # 增加超时时间到3分钟
                )
                self.logger.info(f"DeepSeek API响应状态码: {response.status_code}")
                self.logger.info(f"响应头: {dict(response.headers)}")
            except requests.exceptions.Timeout:
                self.logger.error("DeepSeek API请求超时（180秒）")
                raise Exception("DeepSeek API请求超时")
            except requests.exceptions.RequestException as e:
                self.logger.error(f"DeepSeek API请求失败: {e}")
                raise Exception(f"DeepSeek API请求失败: {e}")

            if response.status_code != 200:
                self.logger.error(f"DeepSeek API错误: {response.status_code} - {response.text}")
                raise Exception(f"DeepSeek API error: {response.status_code} - {response.text}")

            self.logger.info("解析DeepSeek API响应...")
            response_data = response.json()
            self.logger.info("解析JSON内容...")
            
            # 打印原始响应内容
            raw_content = response_data["choices"][0]["message"]["content"]
            self.logger.info(f"DeepSeek API原始响应内容长度: {len(raw_content)} 字符")
            self.logger.info(f"原始响应内容预览: {raw_content[:500]}...")
            
            try:
                graph_data = json.loads(raw_content)
                self.logger.info(f"成功解析图谱数据，包含 {len(graph_data.get('nodes', []))} 个节点，{len(graph_data.get('edges', []))} 个边")
                
                # 详细调试输出
                self.logger.info("\n=== 节点信息 ===")
                for i, node in enumerate(graph_data.get('nodes', [])[:3]):  # 只显示前3个节点
                    self.logger.info(f"节点{i+1}: {node.get('id', 'N/A')} - {node.get('type', 'N/A')}")
                
                self.logger.info("\n=== 边信息 ===")
                edges = graph_data.get('edges', [])
                if edges:
                    for i, edge in enumerate(edges[:3]):  # 只显示前3个边
                        self.logger.info(f"边{i+1}: {edge.get('source_id', 'N/A')} -> {edge.get('target_id', 'N/A')} ({edge.get('type', 'N/A')})")
                else:
                    self.logger.warning("⚠️ 没有找到任何边关系！")
                    
                # 打印完整的JSON结构，看看是否有其他字段
                self.logger.info("\n=== 完整JSON结构 ===")
                self.logger.info(f"JSON根字段: {list(graph_data.keys())}")
                for key, value in graph_data.items():
                    if isinstance(value, list):
                        self.logger.info(f"字段 '{key}': {len(value)} 个元素")
                    else:
                        self.logger.info(f"字段 '{key}': {type(value)}")
                    
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败: {e}")
                self.logger.error(f"原始内容: {raw_content}")
                raise Exception(f"JSON解析失败: {e}")

            # 转换为LightRAG的数据结构
            nodes = []
            for node_data in graph_data.get("nodes", []):
                props = node_data.get('properties', {})
                props['entity_id'] = node_data['id']
                props['entity_type'] = node_data['type']
                self.logger.info(f"entity_type: { props['entity_type']}")
                nodes.append(Node(
                    id=node_data['id'],
                    labels=[node_data['type']],
                    properties=props
                ))

            edges = []
            for edge_data in graph_data.get("edges", []):
                source = edge_data['source_id']
                target = edge_data['target_id']
                edge_type = edge_data['type']
                edge_id = f"{source}_{edge_type}_{target}"
                edge_properties = edge_data.get('properties', {})
                edges.append(Edge(
                    id=edge_id,
                    source=source,
                    target=target,
                    type=edge_type,
                    properties=edge_properties
                ))

            return Graph(nodes=nodes, edges=edges)
        except Exception as e:
            self.logger.error(f"Error extracting graph from text: {e}")
            raise

    def _split_text_into_chunks(self, text: str, chunk_size: int = 6000, overlap: int = 1000) -> List[str]:
        """
        将长文本分割成重叠的块
        
        Args:
            text: 输入文本
            chunk_size: 每块的大小
            overlap: 重叠部分的大小
            
        Returns:
            List[str]: 文本块列表
        """
        self.logger.info(f"_split_text_into_chunks: 开始分块，文本长度={len(text)}, chunk_size={chunk_size}, overlap={overlap}")
        
        if not text:
            self.logger.warning("输入文本为空，返回空列表")
            return []
            
        # 确保重叠部分小于块大小
        if overlap >= chunk_size:
            self.logger.warning(f"重叠部分({overlap})大于等于块大小({chunk_size})，调整为块大小的一半")
            overlap = chunk_size // 2
            
        chunks = []
        start = 0
        chunk_count = 0
        
        self.logger.info(f"开始循环分块，初始start={start}, 文本长度={len(text)}, 调整后overlap={overlap}")
        
        max_iterations = 1000  # 防止无限循环
        iteration_count = 0
        
        while start < len(text) and iteration_count < max_iterations:
            iteration_count += 1
            end = start + chunk_size
            if end > len(text):
                end = len(text)
            
            chunk = text[start:end]
            chunks.append(chunk)
            chunk_count += 1
            self.logger.info(f"创建第{chunk_count}个块: start={start}, end={end}, 长度={len(chunk)}")
            
            # 计算下一个起始位置
            if end >= len(text):
                # 如果已经到达文本末尾，说明处理完成
                self.logger.info(f"分块完成，已到达文本末尾: end={end}, len(text)={len(text)}")
                break
            else:
                # 正常情况：计算下一个起始位置
                start = end - overlap
                # 确保至少前进一个字符
                if start <= end - chunk_size:
                    self.logger.warning(f"下一个起始位置({start})没有前进，强制前进1个字符")
                    start = end - chunk_size + 1
                
        if iteration_count >= max_iterations:
            self.logger.warning(f"达到最大迭代次数({max_iterations})，强制停止分块")
            
        self.logger.info(f"_split_text_into_chunks: 分块完成，共创建{len(chunks)}个块，迭代次数={iteration_count}")
        return chunks

    async def build_and_store_graph(
        self,
        text: str,
        course_name: str,
        filename: str,
        clear_existing: bool = False,
        debug: bool = False,
        use_chunking: bool = True
    ) -> None:
        """
        构建并存储知识图谱
        
        Args:
            text: 输入文本
            course_name: 课程名称
            clear_existing: 是否清空现有数据
            debug: 是否打印调试信息
            use_chunking: 是否使用分块处理
        """
        # if debug:
        #     self.logger.setLevel(logging.DEBUG)

        try:
            self.logger.info("开始构建知识图谱...")
            
            # 初始化
            self.logger.info("正在初始化...")
            await self.async_init()
            self.logger.info("初始化完成")
            
            # 测试Neo4j连接
            connection_ok = await self.test_connection()
            if not connection_ok:
                self.logger.error("Neo4j连接失败，跳过知识图谱生成")
                return
            
            # 如果需要，清空数据库
            if clear_existing:
                self.logger.info("Clearing existing database...")
                await self.clear_database()

            self.logger.info("开始处理文本...")
            self.logger.info(f"文本总长度: {len(text)} 字符")
            
            if use_chunking and len(text) > 6000:
                # 对于长文本，直接使用分块处理
                self.logger.info(f"Text is long ({len(text)} chars), using chunking directly...")
                
                chunks = self._split_text_into_chunks(text, chunk_size=6000, overlap=1000)
                self.logger.info(f"Split into {len(chunks)} chunks")
                self.logger.info(f"每块大小: 6000字符，重叠: 1000字符")
                
                # 处理所有块
                self.logger.info(f"开始处理所有{len(chunks)}个块...")
                all_nodes = []
                all_edges = []
                
                for i, chunk in enumerate(chunks):
                    try:
                        self.logger.info(f"处理第{i+1}/{len(chunks)}个块，长度: {len(chunk)} 字符")
                        self.logger.info(f"第{i+1}个块内容预览: {chunk[:200]}...")
                        
                        self.logger.info(f"开始调用DeepSeek API处理第{i+1}个块...")
                        graph = self._extract_graph_from_text(chunk, course_name)
                        self.logger.info(f"DeepSeek API调用完成，第{i+1}个块")
                        
                        if graph.nodes:
                            self.logger.info(f"第{i+1}个块: 提取了 {len(graph.nodes)} 个节点")
                            all_nodes.extend(graph.nodes)
                        if graph.edges:
                            self.logger.info(f"第{i+1}个块: 提取了 {len(graph.edges)} 个边")
                            all_edges.extend(graph.edges)
                        
                        self.logger.info(f"第{i+1}个块处理完成，累计节点: {len(all_nodes)}, 累计边: {len(all_edges)}")
                        
                    except Exception as e:
                        self.logger.error(f"处理第{i+1}个块时出错: {e}")
                        import traceback
                        traceback.print_exc()
                        continue  # 继续处理下一个块
                
                # 合并所有节点和边
                graph = Graph(nodes=all_nodes, edges=all_edges)
                self.logger.info(f"所有块处理完成，Total extracted: {len(all_nodes)} nodes, {len(all_edges)} edges")

                merged_graph_data = self._merge_graph_with_deepseek(all_nodes, all_edges)
                # 解析合并后的节点和边
                nodes = [Node(**n) for n in merged_graph_data.get("nodes",[])]
                edges = [Edge(**e) for e in merged_graph_data.get("edges",[])]
                graph = Graph(nodes=nodes, edges=edges)
                self.logger.info(merged_graph_data)

            else:
                # 直接处理短文本
                self.logger.info("Extracting knowledge graph from text...")
                graph = self._extract_graph_from_text(text, course_name)
            
            if not (graph.nodes or graph.edges):
                self.logger.warning("No graph data extracted from text.")
                return
            
            graph= self._optimize_graph_structure(graph, filename)

            # 存储节点和边
            self.logger.info(f"Storing {len(graph.nodes)} nodes and {len(graph.edges)} edges...")
            
            # 存储节点
            stored_nodes = 0
            for i, node in enumerate(graph.nodes):
                # if debug:
                #     self.logger.debug(f"\n节点信息:")
                #     self.logger.debug(f"ID: {node.id}")
                #     self.logger.debug(f"标签: {node.labels}")
                #     self.logger.debug(f"属性: {node.properties}")
                try:
                    await self.graph_store.upsert_node(node.id, node.properties)
                    stored_nodes += 1
                    if (i + 1) % 10 == 0:  # 每10个节点报告一次进度
                        self.logger.info(f"Stored {stored_nodes}/{len(graph.nodes)} nodes...")
                except Exception as e:
                    self.logger.error(f"Error storing node {node.id}: {e}")
                    continue

                self.logger.info(f"Successfully stored {stored_nodes}/{len(graph.nodes)} nodes")

                # 存储边
                stored_edges = 0
                for i, edge in enumerate(graph.edges):
                    # if debug:
                    #     self.logger.debug(f"\n关系信息:")
                    #     self.logger.debug(f"源节点: {edge.source}")
                    #     self.logger.debug(f"目标节点: {edge.target}")
                    #     self.logger.debug(f"关系类型: {edge.type}")
                    #     self.logger.debug(f"关系属性: {edge.properties}")

                    # 构建Cypher查询
                    cypher = (
                        f"MATCH (source) WHERE source.entity_id = $source_id "
                        f"MATCH (target) WHERE target.entity_id = $target_id "
                        f"MERGE (source)-[r:{edge.type}]->(target) "
                        f"SET r += $properties "
                        f"RETURN type(r) as relationType"
                    )

                    # if debug:
                    #     self.logger.debug(f"\n执行的Cypher查询:")
                    #     self.logger.debug(cypher)
                    #     self.logger.debug(f"参数: source_id={edge.source}, target_id={edge.target}, properties={edge.properties}")

                    try:
                        async with self.driver.session(database="neo4j") as session:
                            result = await session.run(
                                cypher,
                                source_id=edge.source,
                                target_id=edge.target,
                                properties=edge.properties
                            )
                            stored_edges += 1
                            if (i + 1) % 20 == 0:  # 每20个边报告一次进度
                                self.logger.info(f"Stored {stored_edges}/{len(graph.edges)} edges...")
                            # if debug:
                            #     records = await result.data()
                            #     self.logger.debug(f"查询结果: {records}")
                    except Exception as e:
                        self.logger.error(f"Error creating relationship: {str(e)}")
                        # if debug:
                        #     import traceback
                        #     traceback.print_exc()
                        continue

                self.logger.info(f"Successfully stored {stored_edges}/{len(graph.edges)} edges")

                self.logger.info("Knowledge graph updated successfully.")
                await self.link_course_root_to_subgraph_roots(course_name)
            
        except Exception as e:
            self.logger.error(f"Error building and storing graph: {e}")
            # if debug:
            #     import traceback
            #     traceback.print_exc()
            raise
        # finally:
            # if debug:
            #     self.logger.setLevel(logging.INFO)

    async def link_course_root_to_subgraph_roots(self, course_name: str):
        """
        将 CourseRoot 节点与所有子图根节点（没有入边的 FileRoot 节点）连接。
        """
        cypher_find_file_roots = """
        MATCH (n {course: $course_name, category: 'FileRoot'})
        WHERE NOT (()-[]->(n))
        RETURN n.entity_id AS sub_root_id
        """

        async with self.driver.session(database="neo4j") as session:
            result = await session.run(cypher_find_file_roots, course_name=course_name)
            records = await result.data()
            sub_roots = [record["sub_root_id"] for record in records]

            for sub_root_id in sub_roots:
                cypher_link = """
                MATCH (root:CourseRoot {course: $course_name})
                MATCH (n {entity_id: $sub_root_id, course: $course_name})
                MERGE (root)-[r:CONTAINS {
                    description: '课程根节点包含文件知识图谱根节点',
                    strength: 'Strong',
                    direction: 'CONTAINS'
                }]->(n)
                """
                await session.run(cypher_link, course_name=course_name, sub_root_id=sub_root_id)

            self.logger.info(f"已将 CourseRoot 与 {len(sub_roots)} 个 FileRoot 节点连接: {sub_roots}")

    def _merge_graph_with_deepseek(self, nodes, edges):
        prompt = f"""
        以 JSON 格式返回\n
        请对以下知识图谱节点和边进行全局合并，要求：
        1. 合并相似/重复节点（如名称、内容、定义高度相似的节点合并为一个，保留最重要的属性）。
        2. 不要生成环，整个图必须是有向无环图（DAG），且尽量只有一个入度为0的根节点。
        3. 删除冗余边（如A->B, B->C, A>C都存在，删除A->C）。
        4. 参考节点的 importance 字段和你自身的知识库，对所有边进行 importance（重要性）排序，不能有并列，必须严格排序（如1,2,3...，1表示最不重要），edges 加入 importance 字段记录排序结果。
        5. 输出合并后的节点和边，格式如下：
        {{
        "nodes": [...],
        "edges": [...
                  "importance": 1/2/3/...]
        }}
        原始节点和边数据如下：
        ---
        {json.dumps({"nodes": [n.dict() for n in nodes], "edges": [e.dict() for e in edges]}, ensure_ascii=False)}
        ---
        """
        # 调用DeepSeek API
        headers = {
            "Authorization": f"Bearer {self.deepseek_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 8000,
            "response_format": {"type": "json_object"}
        }
        response = requests.post(
            f"{self.deepseek_base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=240
        )
        if response.status_code != 200:
            raise Exception(f"DeepSeek API error: {response.status_code} - {response.text}")
        response_data = response.json()
        raw_content = response_data["choices"][0]["message"]["content"]
        merged_graph_data = json.loads(raw_content)
        print(merged_graph_data)
        return merged_graph_data

    def _optimize_graph_structure(self, graph, filename: str):
        """
        对合并后的知识图谱进行结构优化：
        1. 删除冗余边（如a->b->c和a->c同时存在时删除a->c）
        2. 检测并破坏环（删除环中importance最小的边）
        3. 选择入度为0且所有出边importance之和最高的点为根节点（并列随便选）
        4. 将根节点连到其他入度为0的点
        """
        # 1. 构建图
        G = nx.DiGraph()
        for node in graph.nodes:
            G.add_node(node.id, node=node)
        for edge in graph.edges:
            importance = edge.properties.get('importance', 1)
            try:
                importance = int(importance)
            except Exception:
                importance = 1
            G.add_edge(edge.source, edge.target, edge=edge, importance=importance)

        # 2. 删除冗余边（如 a->b->c 和 a->c 同时存在）
        to_remove = set()
        edges = list(G.edges(data=True))
        for u, v, attr in edges:
            G.remove_edge(u, v)
            if nx.has_path(G, u, v):  # 如果去掉这条边后还有路径，则冗余
                to_remove.add((u, v))
            G.add_edge(u, v, **attr)  # 恢复边
        for u, v in to_remove:
            G.remove_edge(u, v)

        # 3. 破坏环（删 importance 最小的边）
        try:
            while not nx.is_directed_acyclic_graph(G):
                cycles = list(nx.simple_cycles(G))
                if not cycles:
                    break
                for cycle in cycles:
                    min_imp = float('inf')
                    min_edge = None
                    for i in range(len(cycle)):
                        u = cycle[i]
                        v = cycle[(i + 1) % len(cycle)]
                        imp = G[u][v]['importance']
                        if imp < min_imp:
                            min_imp = imp
                            min_edge = (u, v)
                    if min_edge:
                        G.remove_edge(*min_edge)
        except Exception as e:
            self.logger.error(f"破坏环时出错: {e}")

        try:
            any_node = next(iter(G.nodes))
            course = G.nodes[any_node]['node'].properties.get('course', '')
        except StopIteration:
            self.logger.error("空图，无法构建 FileRoot")
            return graph

        # 4. 新建一个人工根节点（以课件 filename 为根）
        from uuid import uuid4
        root_node = Node(
            id=f"fileroot_{filename}",
            labels=["FileRoot"],
            properties={
                "entity_type": "FileRoot",
                "entity_id": f"fileroot_{filename}",
                "name": filename,
                "course": course,
                "description": f"{filename} 根节点",
                "content": f"课件 {filename} 根节点",
                "importance": "High",
                "category": "FileRoot"
            }
        )
        G.add_node(filename, node=root_node)

        # 5. 连接入度为0的原始节点
        in_deg0_nodes = [n for n in G.nodes if G.in_degree(n) == 0 and n != filename]
        for target_id in in_deg0_nodes:
            edge_id = f"{filename}_CONTAINS_{target_id}_from_file"
            edge = Edge(
                id=edge_id,
                source=f"fileroot_{filename}",
                target=target_id,
                type="CONTAINS",
                properties={
                    "description": "{filename}包含知识点",
                    "strength": "Strong",
                    "direction": "Forward",
                }
            )
            G.add_edge(filename, target_id, edge=edge, importance=0)

        # 6. 返回新的图结构
        nodes = [G.nodes[n]['node'] for n in G.nodes if 'node' in G.nodes[n]]
        edges = [G[u][v]['edge'] for u, v in G.edges]
        return type(graph)(nodes=nodes, edges=edges)