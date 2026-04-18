from langchain_text_splitters import RecursiveCharacterTextSplitter
from repository.vector_repository import VectorRepository
from typing import List, Dict, Tuple


class VectorDAO:
    """向量数据访问对象，负责向量相关的业务逻辑"""

    def __init__(self, embedding, db_path: str = "./chroma_db", collection_name: str = "rag_collection"):
        """
        初始化VectorDAO，使用ChromaDB作为后端
        :param embedding: LangChain的嵌入模型实例
        :param db_path: ChromaDB持久化存储的路径
        :param collection_name: ChromaDB中的集合名称
        """
        self.collection_name = collection_name
        self.vector_repository = VectorRepository(
            path=db_path,
            collection_name=collection_name,
            embedding_function=embedding
        )
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    def split_text(self, text: str) -> List[str]:
        """将长文本分割为适合处理的片段"""
        return self.text_splitter.split_text(text)

    def load(self):
        """加载向量存储。对于ChromaDB，此操作是自动的，无需手动调用。"""
        print("ChromaDB client is persistent. No explicit load action needed.")
        return True

    def save(self):
        """保存向量存储。对于ChromaDB，此操作是自动的，无需手动调用。"""
        print("ChromaDB client is persistent. No explicit save action needed.")
        return True

    def add(self, chunks: List[str], metadatas: List[Dict]):
        """添加文本块到向量存储"""
        return self.vector_repository.add_texts(chunks, metadatas)

    def search(self, query: str, k: int = 3, course_name: str = None):
        """搜索相似文档"""
        return self.vector_repository.similarity_search(query, k, course_name=course_name)

    def _get_all_documents(self) -> Dict[str, List]:
        """获取所有文档信息"""
        return self.vector_repository._get_all_documents()

    def delete_by_source(self, source: str) -> bool:
        """
        根据文件源删除对应的向量。
        直接调用repository的高效删除方法。
        """
        return self.vector_repository.delete_by_source(source)

    def get_document_count(self) -> int:
        """获取当前向量存储中的文档数量"""
        return self.vector_repository.get_document_count()

    def list_sources(self) -> List[str]:
        """获取所有文档源（文件ID）的列表"""
        try:
            all_docs = self._get_all_documents()
            sources = set()
            for metadata in all_docs.get('metadatas', []):
                if 'source' in metadata:
                    sources.add(metadata['source'])
            return list(sources)
        except Exception:
            return []

    def get_vector_info(self) -> dict:
        """获取向量存储的详细信息"""
        return self.vector_repository.get_vector_info()

    def get_by_filename(self, filename: str):
        return self.vector_repository.get_by_filename(filename)

    def get_by_filename_and_page(self, filename: str, page_idx: int):
        return self.vector_repository.get_by_filename_and_page(filename, page_idx)

    def get_by_course(self, course: str):
        return self.vector_repository.get_by_course(course)

    def get_by_course_and_filename(self, course: str, filename: str):
        return self.vector_repository.get_by_course_and_filename(course, filename)

    def get_by_course_filename_and_page(self, course: str, filename: str, page_idx: int):
        return self.vector_repository.get_by_course_filename_and_page(course, filename, page_idx)
