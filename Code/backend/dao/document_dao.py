# dao/document_dao.py
from repository.document_repository import DocumentRepository
from repository.document_parser_repository import DocumentParserRepository
from typing import Optional, Dict, Any, List, Tuple


class DocumentDAO:
    def __init__(self, document_repository: DocumentRepository, document_parser_repository: DocumentParserRepository):
        self.document_repository = document_repository
        self.document_parser_repository = document_parser_repository
    
    def save_file_to_mongo(self, file_content: bytes, filename: str, course_name: str) -> str:
        """
        通过repository保存文件到MongoDB并返回文件ID
        :param file_content: 文件内容
        :param filename: 文件名
        :param course_name: 课程名称
        :return: 文件ID
        """
        metadata = {"course": course_name}
        file_id = self.document_repository.save_file(file_content, filename, metadata)
        return file_id

    def get_documents_by_course(self, course_name: str, page: int, size: int):
        documents = self.document_repository.get_documents_by_course(course_name, page, size)

        result = []
        for doc in documents["items"]:
            result.append({
                "file_id": str(doc["_id"]),
                "filename": doc.get("filename"),
                "upload_time": doc.get("uploadDate").strftime("%Y-%m-%d %H:%M:%S") if doc.get("uploadDate") else None,
                "course": doc.get("metadata", {}).get("course"),
                "size": doc.get("length", 0)  # 这里加上文件大小，单位是字节
            })
        return result, documents["total"]

    def get_file_stream(self, file_id: str):
        return self.document_repository.get_file_stream(file_id)
    def get_file_by_id(self, file_id: str):
        return self.document_repository.get_file(file_id)
    def get_documents_by_course(self, course_name: str, page: int, size: int):
        documents = self.document_repository.get_documents_by_course(course_name, page, size)

        result = []
        for doc in documents["items"]:
            result.append({
                "file_id": str(doc["_id"]),
                "filename": doc.get("filename"),
                "upload_time": doc.get("uploadDate").strftime("%Y-%m-%d %H:%M:%S") if doc.get("uploadDate") else None,
                "course": doc.get("metadata", {}).get("course"),
                "size": doc.get("length", 0)  # 这里加上文件大小，单位是字节
            })
        return result, documents["total"]

    def get_file_from_mongo(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        通过repository从MongoDB获取文件
        :param file_id: 文件ID
        :return: 文件信息字典
        """
        return self.document_repository.get_file(file_id)
    
    def delete_file_from_mongo(self, file_id: str) -> bool:
        """
        通过repository从MongoDB删除文件
        :param file_id: 文件ID
        :return: 是否删除成功
        """
        return self.document_repository.delete_file(file_id)
    
    def extract_text_from_file(self, file_id: str) -> str:
        """
        通过repository从文件中提取文本（使用传统方法）
        :param file_id: 文件ID
        :return: 提取的文本内容
        """
        return self.document_repository.extract_text(file_id)

    def parse_document_with_mineru(self, file_content: bytes, filename: str, output_dir: str = "./output", parse_method: str = "auto") -> Tuple[List[Dict[str, Any]], str]:
        """
        使用MinerU解析文档
        :param file_content: 文件内容
        :param filename: 文件名
        :param output_dir: 输出目录
        :param parse_method: 解析方法
        :return: (content_list, md_content) 内容列表和markdown文本
        """
        return self.document_parser_repository.parse_document(
            file_content=file_content,
            filename=filename,
            output_dir=output_dir,
            parse_method=parse_method
        )

    def process_content_with_vision(self, content_list: List[Dict[str, Any]], output_dir: str) -> str:
        """
        使用视觉模型处理内容（图片、表格、公式）
        :param content_list: 内容列表
        :param output_dir: 输出目录
        :return: 处理后的文本内容
        """
        from pathlib import Path
        return self.document_parser_repository.process_content_by_order(
            content_list=content_list,
            output_dir=Path(output_dir)
        )

    def get_all_files_from_mongo(self) -> list:
        """
        通过repository从MongoDB获取所有文件
        :return: 文件信息列表
        """
        return self.document_repository.get_all_files()
