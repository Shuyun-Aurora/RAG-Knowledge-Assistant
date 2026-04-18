import chromadb
from chromadb.types import Where
from langchain_core.documents import Document
from typing import List, Dict, Tuple, Optional
import uuid


class VectorRepository:
    """向量存储仓库层，负责与 ChromaDB 向量数据库的直接交互"""

    def __init__(self, path: str, collection_name: str, embedding_function):
        """
        初始化ChromaDB客户端
        :param path: 数据库文件持久化路径
        :param collection_name: 要操作的集合名称
        :param embedding_function: LangChain的嵌入函数
        """
        # 使用PersistentClient实现数据持久化到磁盘
        self.client = chromadb.PersistentClient(path=path)

        # 将LangChain的embedding函数适配到ChromaDB
        self.chroma_embedding_function = chromadb.utils.embedding_functions.ChromaLangchainEmbeddingFunction(
            embedding_function)

        # 获取或创建集合，并指定嵌入函数
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.chroma_embedding_function,
            metadata={
                "hnsw:space": "cosine"  # 明确指定使用余弦相似度
            }
        )

    def add_texts(self, chunks: List[str], metadatas: List[Dict]) -> bool:
        """
        向ChromaDB集合中添加文本块。
        Chroma需要为每个文档提供唯一的ID。
        """
        if not chunks:
            return True

        # 为每个chunk生成一个唯一的ID，这是ChromaDB所必需的
        ids = [str(uuid.uuid4()) for _ in chunks]

        try:
            self.collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            print(f"成功向集合 '{self.collection.name}' 添加了 {len(chunks)} 个向量。")
            return True
        except Exception as e:
            print(f"添加文本到ChromaDB时出错: {e}")
            return False

    def similarity_search(self, query: str, k: int = 3, course_name: str = None) -> List[Tuple[Document, float]]:
        """
        在ChromaDB中执行相似性搜索。
        如果指定course_name，则只在该课程下检索。
        """
        try:
            where = None
            if course_name:
                where = {"course": course_name}
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                include=["documents", "metadatas", "distances"],
                where=where
            )
            docs_with_distances = []
            if results and results['ids'][0]:
                ids = results['ids'][0]
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]

                for i in range(len(ids)):
                    doc = Document(page_content=documents[i], metadata=metadatas[i])
                    distance = distances[i]
                    print(f"distance[{i}]: {distance}")
                    docs_with_distances.append((doc, distance))

            return docs_with_distances
        except Exception as e:
            print(f"ChromaDB相似性搜索时出错: {e}")
            return []

    def delete_by_source(self, source: str) -> bool:
        """
        根据文件源 (source) 在元数据中过滤并删除向量。
        这是ChromaDB的巨大优势：高效的元数据过滤删除。
        """
        try:
            # 使用 where 条件来指定要删除的文档
            where_filter: Where = {"source": source}
            self.collection.delete(where=where_filter)
            print(f"已成功提交删除源为 '{source}' 的向量的任务。")
            return True
        except Exception as e:
            print(f"从ChromaDB删除向量时出错: {e}")
            return False

    def get_document_count(self) -> int:
        """获取当前集合中的向量数量"""
        try:
            return self.collection.count()
        except Exception as e:
            print(f"获取ChromaDB文档数量时出错: {e}")
            return 0

    def _get_all_documents(self) -> Dict[str, List]:
        """获取集合中所有文档的信息（主要用于list_sources）"""
        try:
            # 获取所有数据，注意如果数据量巨大，这可能会消耗很多内存
            # 对于list_sources，我们只需要metadatas
            results = self.collection.get(include=["metadatas"])
            return {"metadatas": results.get('metadatas', [])}
        except Exception as e:
            print(f"从ChromaDB获取所有文档时出错: {e}")
            return {"metadatas": []}

    def get_vector_info(self) -> Dict:
        """获取向量存储的详细信息"""
        try:
            return {
                "vector_count": self.collection.count(),
                "collection_name": self.collection.name,
                "database_path": self.client._path
            }
        except Exception as e:
            return {"error": str(e)}

    def get_by_filename(self, filename: str) -> List[Document]:
        where = {"filename": filename}
        results = self.collection.get(where=where, include=["documents", "metadatas"])
        docs = []
        for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
            docs.append(Document(page_content=doc, metadata=meta))
        return docs

    def get_by_filename_and_page(self, filename: str, page_idx: int) -> List[Document]:
        # 只用filename查
        where = {"filename": filename}
        results = self.collection.get(where=where, include=["documents", "metadatas"])
        docs = []
        for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
            sp = meta.get("start_page")
            ep = meta.get("end_page")
            # 类型安全
            if isinstance(sp, str):
                try:
                    sp = int(sp)
                except Exception:
                    continue
            if isinstance(ep, str):
                try:
                    ep = int(ep)
                except Exception:
                    continue
            if sp is not None and ep is not None and sp <= page_idx <= ep:
                docs.append(Document(page_content=doc, metadata=meta))
        return docs

    def get_by_course(self, course: str) -> List[Document]:
        where = {"course": course}
        results = self.collection.get(where=where, include=["documents", "metadatas"])
        docs = []
        for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
            docs.append(Document(page_content=doc, metadata=meta))
        return docs

    def get_by_course_and_filename(self, course: str, filename: str) -> List[Document]:
        # 先查course
        where = {"course": course}
        results = self.collection.get(where=where, include=["documents", "metadatas"])
        docs = []
        for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
            if meta.get("filename") == filename:
                docs.append(Document(page_content=doc, metadata=meta))
        return docs

    def get_by_course_filename_and_page(self, course: str, filename: str, page_idx: int) -> List[Document]:
        # 先查course
        where = {"course": course}
        results = self.collection.get(where=where, include=["documents", "metadatas"])
        docs = []
        for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
            if meta.get("filename") == filename:
                sp = meta.get("start_page")
                ep = meta.get("end_page")
                if isinstance(sp, str):
                    try:
                        sp = int(sp)
                    except Exception:
                        continue
                if isinstance(ep, str):
                    try:
                        ep = int(ep)
                    except Exception:
                        continue
                if sp is not None and ep is not None and sp <= page_idx <= ep:
                    docs.append(Document(page_content=doc, metadata=meta))
        return docs