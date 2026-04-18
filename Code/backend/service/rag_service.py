# app/service/rag_service.py

import asyncio
from dao.document_dao import DocumentDAO
from typing import AsyncGenerator, List, Dict, Any
from langchain_core.messages import messages_from_dict, messages_to_dict, HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from service.LightRAGKnowledgeGraph_generate_service import LightRAGKnowledgeGraph
from service.knowledge_graph_service import KnowledgeGraphService
from config.settings import settings
from service.agent_service import AgentService
from dto.schemas import AgentStyle
from dao.vector_dao import VectorDAO
from repository.embedding_repository import QwenEmbeddings
from repository.llm_repository import DeepSeekLLM
from repository.document_repository import DocumentRepository
from repository.document_parser_repository import DocumentParserRepository
from dao.chat_history_dao import ChatHistoryDAO
from repository.chat_history_repository import ChatHistoryRepository
from dao.knowledge_graph_dao import KnowledgeGraphDAO
import shutil

class RAGService:
    def __init__(self, vector_dao, llm, document_dao: DocumentDAO, chat_history_dao, knowledge_graph_service: KnowledgeGraphService = None):
        self.vector_dao = vector_dao
        self.llm = llm
        self.document_dao = document_dao
        self.chat_history_dao = chat_history_dao
        self.knowledge_graph_service = knowledge_graph_service
        self.agent_service = AgentService()  # 新增

    def _clean_data_for_bson(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {key: self._clean_data_for_bson(value) for key, value in data.items()}
        if isinstance(data, list):
            return [self._clean_data_for_bson(item) for item in data]
        if isinstance(data, (int, float, str, bool, bytes)) or data is None:
            return data
        try:
            json.dumps(data)
            return data
        except (TypeError, OverflowError):
            return str(data)

    # --- 原有的文档上传方法 ---
    def upload_document(self, file_content: bytes, filename: str, course_name: str) -> str:
        file_id = self.document_dao.save_file_to_mongo(file_content, filename, course_name)
        self.add_document(file_id, course_name)
        return file_id

    def add_document(self, file_id: str, course: str):
        text = self.document_dao.extract_text_from_file(file_id)
        chunks = self.vector_dao.split_text(text)
        metadatas = [{"source": file_id, "course": course} for _ in chunks]
        self.vector_dao.add(chunks, metadatas)
        self.vector_dao.save()

    def upload_document_batch(self, files: List[dict], course_name: str) -> List[str]:
        """
        同步保存文档内容到 MongoDB，并将解析任务交给后台处理。
        """
        file_ids = []

        for f in files:
            try:
                file_id = self.document_dao.save_file_to_mongo(f["file_content"], f["filename"], course_name)
                file_ids.append(file_id)
                # 后台任务异步执行 add_document
                self._submit_async_add(file_id, course_name)
            except Exception as e:
                print(f"[错误] 上传文件 {f['filename']} 失败: {e}")

        return file_ids

    from concurrent.futures import ThreadPoolExecutor

    _executor = ThreadPoolExecutor(max_workers=4)  # 线程池开4个线程

    def _submit_async_add(self, file_id: str, course_name: str):
        """
        提交异步任务进行解析和向量入库
        """

        def task():
            try:
                self.add_document(file_id, course_name)
                print(f"[后台任务] 处理完成: {file_id}")
            except Exception as e:
                print(f"[后台任务] 解析文件 {file_id} 失败: {e}")

        self._executor.submit(task)

    def submit_multimodal_processing(
        self,
        file_content: bytes,
        filename: str,
        course_name: str,
        parse_method: str,
        file_id: str,
        generate_knowledge_graph: bool,
    ):
        def task():
            try:
                success = self.process_one_file_async(
                    file_content,
                    filename,
                    course_name,
                    parse_method,
                    file_id,
                    generate_knowledge_graph,
                )
                if success:
                    print(f"[background task] processed multimodal file successfully: {filename}")
                else:
                    print(f"[background task] failed to process multimodal file: {filename}")
            except SystemExit as e:
                if e.code == 0:
                    print(f"[background task] MinerU exited normally: {filename}")
                else:
                    print(f"[background task] MinerU exited abnormally ({e.code}): {filename}")
            except Exception as e:
                print(f"[background task] failed multimodal file {filename}: {e}")

        self._executor.submit(task)

    async def upload_document_multimodal_batch(
        self,
        files: List[dict],
        course_name: str,
        parse_method: str = "auto",
        generate_knowledge_graph: bool = True,
    ) -> List[str]:
        file_ids = []

        for f in files:
            try:
                file_id = self.document_dao.save_file_to_mongo(
                    f["file_content"], f["filename"], course_name
                )
                file_ids.append(file_id)
                self.submit_multimodal_processing(
                    f["file_content"],
                    f["filename"],
                    course_name,
                    parse_method,
                    file_id,
                    generate_knowledge_graph,
                )
            except Exception as e:
                print(f"[error] batch upload failed for {f['filename']}: {e}")

        return file_ids

    def process_one_file_async(self, file_content: bytes, filename: str, course_name: str,
                               parse_method: str, file_id: str, generate_knowledge_graph: bool):
        """
            后台处理多模态解析任务 + 并调用生成知识图谱函数
        """

        try:
            output_dir = f"./output/{Path(filename).stem}/{parse_method}"
            content_list, md_content = self.document_dao.parse_document_with_mineru(
                file_content=file_content,
                filename=filename,
                output_dir=output_dir,
                parse_method=parse_method
            )

            processed_chunks, kg_text = self.document_dao.process_content_with_vision(
                content_list=content_list,
                output_dir=output_dir
            )

            texts = [chunk["text"] for chunk in processed_chunks]
            metadatas = [{
                "source": file_id,
                "filename": filename,
                "course": course_name,
                "parse_method": parse_method,
                "start_page": min(chunk["page_indices"]) if chunk["page_indices"] else None,
                "end_page": max(chunk["page_indices"]) if chunk["page_indices"] else None
            } for chunk in processed_chunks]

            self.vector_dao.add(texts, metadatas)
            self.vector_dao.save()

            if generate_knowledge_graph and kg_text.strip():
                import asyncio
                asyncio.run(self._generate_knowledge_graph_background(
                    [kg_text], course_name, False, filename
                ))

            print(f"✅ 文件处理完成: {filename}")
            return True

        except Exception as e:
            print(f"❌ 文件解析失败: {filename}，错误: {e}")
            return False

    def get_documents_by_course(self, course_name: str, page: int, size: int):
        return self.document_dao.get_documents_by_course(course_name, page, size)

    def get_file_stream(self, file_id: str):
        return self.document_dao.get_file_stream(file_id)
    def get_file_by_id(self, file_id: str):
        return self.document_dao.get_file_by_id(file_id)

    # --- 新增的MinerU文档上传方法 ---
    async def upload_document_with_mineru(self, file_content: bytes, filename: str, course_name: str, parse_method: str = "auto", generate_knowledge_graph: bool = True, fast_mode: bool = False) -> str:
        """
        使用MinerU解析器上传文档，支持图片、表格、公式的视觉分析

        Args:
            file_content: 文件内容
            filename: 文件名
            course_name: 课程名称
            parse_method: 解析方法 ("auto", "ocr", "layout", "table")

        Returns:
            file_id: 文件ID
        """
        file_id = self.document_dao.save_file_to_mongo(file_content, filename, course_name)

        output_dir = f"./output/{Path(filename).stem}/{parse_method}"
        content_list, md_content = self.document_dao.parse_document_with_mineru(
            file_content=file_content,
            filename=filename,
            output_dir=output_dir,
            parse_method=parse_method
        )

        processed_chunks, kg_text = self.document_dao.process_content_with_vision(
            content_list=content_list,
            output_dir=output_dir
        )

        texts = [chunk["text"] for chunk in processed_chunks]
        metadatas = [{
            "source": file_id,
            "filename": filename,
            "course": course_name,
            "parse_method": parse_method,
            "start_page": min(chunk["page_indices"]) if chunk["page_indices"] else None,
            "end_page": max(chunk["page_indices"]) if chunk["page_indices"] else None
        } for chunk in processed_chunks]
        self.vector_dao.add(texts, metadatas)
        self.vector_dao.save()

        # 知识图谱生成（后台异步进行）
        if generate_knowledge_graph and kg_text.strip():
            # 创建后台任务，不阻塞主流程
            import asyncio
            asyncio.create_task(self._generate_knowledge_graph_background([kg_text], course_name, fast_mode, filename))

        return file_id

    def delete_document(self, file_id: str) -> dict:
        try:
            # 获取文件信息
            file_info = self.document_dao.get_file_by_id(file_id)
            if not file_info:
                return {"success": False, "message": f"文件 '{file_id}' 在数据库中未找到。"}
            
            filename = file_info.get("filename", "")
            course_name = file_info.get("metadata", {}).get("course", "")
            
            # 删除MongoDB中的文件
            file_deleted = self.document_dao.delete_file_from_mongo(file_id)
            if not file_deleted:
                return {"success": False, "message": f"文件 '{file_id}' 删除失败。"}
            
            # 删除向量数据库中的向量
            self.vector_dao.delete_by_source(file_id)
            
            # 删除知识图谱中的相关节点
            kg_delete_result = {"success": False, "message": "知识图谱服务未初始化"}
            if self.knowledge_graph_service and filename and course_name:
                try:
                    # 删除Neo4j中的知识图谱节点
                    kg_delete_result = self.knowledge_graph_service.delete_nodes_by_filename(filename, course_name)
                    
                    # 删除kg_collection中的向量
                    kg_vector_delete_result = self.knowledge_graph_service.delete_kg_vectors_by_filename(filename, course_name)
                    
                    if kg_delete_result["success"]:
                        print(f"知识图谱删除结果: {kg_delete_result['message']}")
                    if kg_vector_delete_result["success"]:
                        print(f"知识图谱向量删除结果: {kg_vector_delete_result['message']}")
                        
                except Exception as e:
                    print(f"删除知识图谱时出错: {e}")
                    kg_delete_result = {"success": False, "message": f"删除知识图谱失败: {str(e)}"}
            
            return {
                "success": True, 
                "message": "文档、向量和知识图谱已成功删除。", 
                "file_id": file_id,
                "filename": filename,
                "course_name": course_name,
                "kg_delete_result": kg_delete_result
            }
        except Exception as e:
            return {"success": False, "message": f"删除过程中发生严重错误: {str(e)}", "file_id": file_id,
                    "error": str(e)}

    def get_document_list(self) -> List[Dict]:
        try:
            sources = self.vector_dao.list_sources()
            documents = []
            for source in sources:
                file_info = self.document_dao.get_file_from_mongo(source)
                if file_info:
                    documents.append({"file_id": source, "filename": file_info.get("filename", "未知"),
                                      "course": file_info.get("metadata", {}).get("course", "未知"),
                                      "upload_time": file_info.get("metadata", {}).get("upload_time", "未知")})
                else:
                    documents.append(
                        {"file_id": source, "filename": "文件已删除", "course": "未知", "status": "孤立向量"})
            return documents
        except Exception as e:
            print(f"获取文档列表时出错: {e}")
            return []

    def get_statistics(self) -> Dict:
        try:
            vector_count = self.vector_dao.get_document_count()
            sources = self.vector_dao.list_sources()
            return {"total_vectors": vector_count, "total_files": len(sources), "vector_sources": sources}
        except Exception as e:
            print(f"获取统计信息时出错: {e}")
            return {"total_vectors": 0, "total_files": 0, "vector_sources": [], "error": str(e)}

    def get_vector_info(self) -> Dict:
        try:
            vector_info = self.vector_dao.get_vector_info()
            return vector_info
        except Exception as e:
            print(f"获取向量信息时出错: {e}")
            return {"error": str(e)}

    def get_chat_history(self, session_id: str, user_id: int = None):
        """
        获取指定会话ID的历史记录
        """
        return self.chat_history_dao.get_chat_history(session_id, user_id)

    def get_user_sessions(self, user_id: int):
        """
        获取用户的所有会话ID
        """
        return self.chat_history_dao.get_user_sessions(user_id)

    def get_user_history_summary(self, user_id: int, limit: int = 50):
        """
        获取用户的历史记录摘要，按时间倒序排列
        """
        return self.chat_history_dao.get_user_history_summary(user_id, limit)

    def get_user_history_summary_by_course(self, user_id: int, course_name: str, limit: int = 50):
        """
        获取用户在指定课程下的历史记录摘要，按时间倒序排列
        """
        return self.chat_history_dao.get_user_history_summary_by_course(user_id, course_name, limit)

    def get_user_courses(self, user_id: int):
        """
        获取用户参与过的所有课程名称
        """
        return self.chat_history_dao.get_user_courses(user_id)

    def delete_session(self, session_id: str, user_id: int):
        """
        删除指定会话（仅限会话所有者）
        """
        return self.chat_history_dao.delete_session(session_id, user_id)

    async def stream_query(self, question: str, session_id: str, user_id: int, course_name: str, filename: str = None, page_idx: int = None, style: str = None):
        """
        流式查询处理，支持可选课程名、文件名和页码过滤embedding。
        """
        # 1. 获取并处理历史对话
        history_dict = self.chat_history_dao.get_chat_history(session_id, user_id)
        history_messages = messages_from_dict(history_dict)
        chat_history = ChatMessageHistory(messages=history_messages)

        # 检查是否是新会话（没有历史记录）
        is_new_session = len(history_messages) == 0
        first_question = question if is_new_session else None

        # --- 从历史记录中提取最近一次的 sources，用于构建更丰富的上下文 ---
        previous_sources = []
        for msg in reversed(chat_history.messages):
            if isinstance(msg, AIMessage) and msg.additional_kwargs.get("sources"):
                previous_sources = msg.additional_kwargs["sources"]
                break

        # 2. 检索相关embedding（全部限定在course_name下）
        if filename and page_idx is not None:
            docs_by_file = self.vector_dao.get_by_course_filename_and_page(course_name, filename, page_idx)
            all_docs = {doc.page_content: doc for doc in docs_by_file}
            # 限制搜索结果数量，避免返回过多文档
            search_results = self.vector_dao.search(question, k=3, course_name=course_name)
            for doc, score in search_results:
                all_docs[doc.page_content] = doc
            sources = list(all_docs.values())
        elif filename:
            docs_by_file = self.vector_dao.get_by_course_and_filename(course_name, filename)
            all_docs = {doc.page_content: doc for doc in docs_by_file}
            # 限制搜索结果数量，避免返回过多文档
            search_results = self.vector_dao.search(question, k=3, course_name=course_name)
            for doc, score in search_results:
                all_docs[doc.page_content] = doc
            sources = list(all_docs.values())
        else:
            docs_with_scores = self.vector_dao.search(question, k=3, course_name=course_name)
            sources = [doc for doc, score in docs_with_scores if score < 0.5]

        # 3. 准备并清理【当前轮次】的 new_sources
        new_sources_raw = [
            {"page_content": doc.page_content, "metadata": doc.metadata}
            for doc in sources
        ]
        new_sources_cleaned = self._clean_data_for_bson(new_sources_raw)

        # 4. 构建用于 LLM Prompt 的合并上下文
        all_sources_dict = {src['page_content']: src for src in previous_sources}
        for src in new_sources_cleaned:
            all_sources_dict[src['page_content']] = src
        final_combined_sources_for_context = list(all_sources_dict.values())

        # 只把本轮检索的sources发给前端
        yield {"type": "source", "data": new_sources_cleaned}

        # 5. 构建RAG上下文
        rag_context = "\n\n".join([src['page_content'] for src in final_combined_sources_for_context])
        history_str = "".join(
            [f"{'用户' if isinstance(msg, HumanMessage) else 'AI'}：{msg.content}\n" for msg in chat_history.messages])

        # 6. 知识图谱增强（如果可用）
        kg_context = ""
        kg_result = None
        if self.knowledge_graph_service:
            try:
                kg_result = await self.knowledge_graph_service.search_related_nodes(
                    query=question,
                    course_name=course_name,
                    top_k=3,
                    include_neighbors=True,
                    neighbor_depth=1,
                    similarity_threshold=0.4
                )
                if kg_result.get("nodes"):
                    kg_context = kg_result["context"]
            except Exception as e:
                print(f"知识图谱搜索失败: {e}")

        # 7. 构建增强的Prompt
        # 处理风格
        agent_style = AgentStyle(style) if style in AgentStyle.__members__.values() or style in AgentStyle._value2member_map_ else AgentStyle.DEFAULT
        prompt = self.agent_service.generate_prompt(
            agent_style,
            rag_context,
            question,
            history_str,
            ("\n知识图谱信息:\n" + kg_context if kg_context else "")
        )
        print(prompt)

        # 8. 记录本轮用户问题
        chat_history.add_user_message(question)

        # 9. 流式生成答案
        answer = ""
        async for chunk in self.llm.stream_invoke(prompt):
            answer += chunk
            yield {"type": "content", "data": chunk}

        # 10. 保存本轮sources和知识图谱信息到历史
        additional_kwargs = {"sources": new_sources_cleaned}

        # 如果有知识图谱信息，也保存到历史中
        if kg_context:
            additional_kwargs["knowledge_graph"] = {
                "context": kg_context,
                "search_info": f"核心节点: {kg_result.get('related_count', 0)} 个, 扩展节点: {kg_result.get('total_nodes', 0) - kg_result.get('related_count', 0)} 个"
            }

        ai_message_with_sources = AIMessage(
            content=answer,
            additional_kwargs=additional_kwargs
        )
        chat_history.messages.append(ai_message_with_sources)

        # 11. 存储最新历史（包含用户ID、课程名称和第一条问题）
        self.chat_history_dao.save_chat_history(
            session_id,
            messages_to_dict(chat_history.messages),
            user_id,
            course_name,
            first_question
        )

    async def _get_knowledge_graph_context(
        self,
        question: str,
        course_name: str,
        top_k: int = 3,
        similarity_threshold: float = 0.3
    ) -> str:
        """
        获取知识图谱上下文信息（高精度检索+图结构扩展）

        Args:
            question: 用户问题
            course_name: 课程名称
            top_k: 返回的节点数量
            similarity_threshold: 相似度阈值，只返回相似度高于此值的节点

        Returns:
            知识图谱上下文字符串
        """
        if not self.knowledge_graph_service:
            return ""

        try:
            # 调用高精度知识图谱搜索方法
            kg_result = await self.knowledge_graph_service.search_related_nodes(
                query=question,
                course_name=course_name,
                top_k=top_k,
                include_neighbors=True,
                neighbor_depth=1,
                similarity_threshold=similarity_threshold
            )

            if kg_result.get("nodes"):
                search_info = kg_result.get("search_info", "")
                print(f"知识图谱搜索成功: {search_info}")
                print(f"核心节点: {kg_result.get('related_count', 0)} 个")
                print(f"扩展节点: {kg_result.get('total_nodes', 0) - kg_result.get('related_count', 0)} 个")
                return kg_result["context"]
            else:
                search_info = kg_result.get("search_info", "未找到相关知识节点")
                print(f"知识图谱搜索: {search_info}")
                return ""

        except Exception as e:
            print(f"知识图谱搜索失败: {e}")
            return ""

    async def enhance_chat_response(
        self,
        question: str,
        course_name: str,
        original_response: str = "",
        rag_context: str = ""
    ) -> str:
        """
        使用知识图谱增强聊天回答

        Args:
            question: 用户问题
            course_name: 课程名称
            original_response: 原始回答（可选）
            rag_context: RAG检索的上下文（可选）

        Returns:
            增强后的回答
        """
        if not self.knowledge_graph_service:
            return original_response

        try:
            # 1. 获取知识图谱上下文
            kg_context = await self._get_knowledge_graph_context(question, course_name)

            if not kg_context:
                return original_response

            # 2. 构建增强提示词
            enhanced_prompt = self._build_enhanced_prompt(
                question=question,
                kg_context=kg_context,
                original_response=original_response,
                rag_context=rag_context
            )

            # 3. 调用LLM生成增强回答
            response = ""
            async for chunk in self.llm.stream_invoke(enhanced_prompt):
                response += chunk

            return response
        except Exception as e:
            print(f"增强聊天回答失败: {e}")
            return original_response

    def _build_enhanced_prompt(
        self,
        question: str,
        kg_context: str,
        original_response: str = "",
        rag_context: str = ""
    ) -> str:
        """构建增强提示词"""
        prompt_parts = [
            "你是一个智能教学助手，现在需要基于知识图谱信息回答用户问题。",
            "",
            f"用户问题: {question}",
            ""
        ]

        if rag_context:
            prompt_parts.extend([
                "## RAG检索的文档内容:",
                rag_context,
                ""
            ])

        if original_response:
            prompt_parts.extend([
                "## 原始回答:",
                original_response,
                ""
            ])

        prompt_parts.extend([
            "## 知识图谱信息:",
            kg_context,
            "",
            "请基于以上信息，特别是知识图谱中的结构化关系，提供准确、详细的回答。",
            "注意利用节点之间的关系来构建完整的知识体系。",
            "回答要求：",
            "1. 准确回答用户问题",
            "2. 利用知识图谱中的概念关系",
            "3. 如果有算法，说明其规则和步骤",
            "4. 如果有概念，说明其定义和相关概念",
            "5. 语言清晰，结构合理"
        ])

        return "\n".join(prompt_parts)


    async def _generate_knowledge_graph_background(self, all_texts: List[str], course_name: str, fast_mode: bool = False, filename: str = None):
        """
        后台异步生成知识图谱，不阻塞主流程
        """
        try:
            print(f"开始为课程 {course_name} 生成知识图谱（后台任务）...")
            print(f"纯文本总长度: {sum(len(text) for text in all_texts)} 字符")
            
            # 初始化知识图谱系统
            kg = LightRAGKnowledgeGraph(
                neo4j_uri=settings.NEO4J_URI,
                neo4j_user=settings.NEO4J_USER,
                neo4j_pass=settings.NEO4J_PASSWORD,
                deepseek_key=settings.DEEPSEEK_API_KEY
            )
            
            try:
                # 将所有纯文本合并
                all_text = "\n\n".join(all_texts)
                
                # 设置超时时间（快速模式2分钟，正常模式5分钟）
                import asyncio
                timeout = 300 if fast_mode else 1200  # 快速模式2分钟，正常模式5分钟
                try:
                    print(f"开始调用知识图谱生成，超时时间: {timeout}秒")
                    await asyncio.wait_for(
                        kg.build_and_store_graph(
                            text=all_text,
                            course_name=course_name,
                            clear_existing=False,  # 不清空现有数据，允许多个文档的图谱共存
                            debug=True,  # 启用详细日志以便调试
                            use_chunking=not fast_mode,  # 快速模式不使用分块处理
                            filename=filename
                        ),
                        timeout=timeout
                    )
                    print(f"课程 {course_name} 知识图谱生成完毕！")
                    
                    # 将知识图谱节点存储到向量数据库
                    await self._store_knowledge_graph_nodes_to_vector_db(course_name, filename)
                    
                except asyncio.TimeoutError:
                    print(f"课程 {course_name} 知识图谱生成超时（{timeout}秒），但文件上传已完成")
                except Exception as e:
                    print(f"知识图谱生成过程中出错: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
            finally:
                # 确保正确关闭连接
                await kg.close()
        except Exception as e:
            print(f"后台生成知识图谱时出错: {str(e)}")
            # 不影响主流程
    
    async def _store_knowledge_graph_nodes_to_vector_db(self, course_name: str, filename: str = None):
        """
        将知识图谱节点存储到kg_collection
        """
        try:
            print(f"开始将课程 {course_name} 的知识图谱节点存储到向量数据库...")
            if not self.knowledge_graph_service:
                print("知识图谱服务未初始化，跳过向量存储")
                return
            kg_data = self.knowledge_graph_service.get_knowledge_graph(limit=1000,course_name=course_name)
            if not kg_data or not kg_data.get("nodes"):
                print(f"课程 {course_name} 没有找到知识图谱节点")
                return
            # 用QwenEmbeddings初始化kg_collection的DAO
            embedding = QwenEmbeddings(settings.DASHSCOPE_API_KEY)
            kg_vector_dao = VectorDAO(embedding, collection_name="kg_collection")
            texts = []
            metadatas = []
            for node in kg_data["nodes"]:
                props = node.get("properties", {})
                # 更健壮地获取字段
                name = props.get("name") or ""
                desc = props.get("description") or ""
                content = props.get("content") or ""
                node_content = f"{name} - {desc} {content}"
                print(f"节点原始数据: {node}")
                print(f"存入向量库的节点内容: {node_content}")
                
                # 根据节点类型设置不同的source
                node_type = props.get("entity_type", "")
                if node_type == "FileRoot":
                    # FileRoot节点使用文件名作为source
                    source = filename if filename else f"knowledge_graph_{course_name}"
                else:
                    # 其他节点使用课程名作为source
                    source = f"knowledge_graph_{course_name}"
                
                metadata = {
                    "type": "knowledge_graph_node",
                    "node_id": str(node.get("id")),
                    "node_name": name,
                    "node_type": node_type,
                    "course": course_name,
                    "source": source,
                    "filename": filename if filename else f"knowledge_graph_{course_name}",
                    "description": desc,
                    "content": content,
                    "importance": props.get("importance", ""),
                    "category": props.get("category", "")
                }
                texts.append(node_content)
                metadatas.append(metadata)
            if texts:
                kg_vector_dao.add(texts, metadatas)
                kg_vector_dao.save()
                print(f"成功将 {len(texts)} 个知识图谱节点存储到kg_collection")
            else:
                print("没有找到有效的知识图谱节点内容")
        except Exception as e:
            print(f"存储知识图谱节点到向量数据库时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def create_course_knowledge_graph_root_node(self, course_name: str):
        """
        新建课程时自动为知识图谱生成一个特殊节点，只有名称字段，名称为课程名。
        """
        try:
            # 创建CourseRoot节点
            node = {
                "id": f"{course_name}_root",
                "labels": ["CourseRoot"],
                "properties": {
                    "entity_type": "CourseRoot",
                    "entity_id": f"{course_name}_root",
                    "importance": "",
                    "name": course_name,
                    "course": course_name,
                    "description": f"课程{course_name}的根节点",
                    "category": "CourseRoot",
                    "content": f"课程{course_name}的根节点"
                }
            }
            
            if self.knowledge_graph_service:
                # 统一走按 entity_id 幂等创建的路径，避免和 LightRAG 的 :base 节点体系产生重复 CourseRoot
                self.knowledge_graph_service.ensure_course_root(course_name)
                print(f"已为课程 {course_name} 自动生成知识图谱根节点")
            else:
                print(f"知识图谱服务未初始化，无法创建CourseRoot节点")
                
        except Exception as e:
            print(f"自动生成课程知识图谱根节点失败: {e}")
            import traceback
            traceback.print_exc()


# embedding/llm
embedding = QwenEmbeddings(settings.DASHSCOPE_API_KEY)
llm = DeepSeekLLM(settings.DEEPSEEK_API_KEY)

# repository
document_repository = DocumentRepository()
document_parser_repository = DocumentParserRepository(settings.DASHSCOPE_API_KEY)

# dao
vector_dao = VectorDAO(embedding=embedding, db_path="./chroma_db")
document_dao = DocumentDAO(document_repository=document_repository, document_parser_repository=document_parser_repository)
chat_history_repository = ChatHistoryRepository(settings.MONGODB_URI, settings.MONGODB_DB)
chat_history_dao = ChatHistoryDAO(chat_history_repository)
knowledge_graph_dao = KnowledgeGraphDAO(
    neo4j_uri=settings.NEO4J_URI,
    neo4j_user=settings.NEO4J_USER,
    neo4j_password=settings.NEO4J_PASSWORD
)
knowledge_graph_service = KnowledgeGraphService(knowledge_graph_dao, vector_dao)

rag_service = RAGService(
    vector_dao=vector_dao,
    llm=llm,
    document_dao=document_dao,
    chat_history_dao=chat_history_dao,
    knowledge_graph_service=knowledge_graph_service
)
