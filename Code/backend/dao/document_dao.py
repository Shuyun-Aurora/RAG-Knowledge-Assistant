from typing import Any, Dict, Optional

from repository.document_repository import DocumentRepository


class DocumentDAO:
    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    def save_file(self, file_content: bytes, filename: str, course_name: str) -> str:
        return self.document_repository.save_file(
            file_content,
            filename,
            {"course": course_name},
        )

    def save_file_to_mongo(self, file_content: bytes, filename: str, course_name: str) -> str:
        return self.save_file(file_content, filename, course_name)

    def get_documents_by_course(self, course_name: str, page: int, size: int):
        documents = self.document_repository.get_documents_by_course(course_name, page, size)
        result = []
        for doc in documents["items"]:
            result.append(
                {
                    "file_id": doc["file_id"],
                    "filename": doc.get("filename"),
                    "upload_time": doc.get("upload_time"),
                    "course": doc.get("metadata", {}).get("course"),
                    "size": doc.get("size", 0),
                }
            )
        return result, documents["total"]

    def get_file_stream(self, file_id: str):
        return self.document_repository.get_file_stream(file_id)

    def get_file_by_id(self, file_id: str):
        return self.document_repository.get_file(file_id)

    def get_file_from_mongo(self, file_id: str) -> Optional[Dict[str, Any]]:
        return self.document_repository.get_file(file_id)

    def delete_file(self, file_id: str) -> bool:
        return self.document_repository.delete_file(file_id)

    def delete_file_from_mongo(self, file_id: str) -> bool:
        return self.delete_file(file_id)

    def get_all_files(self):
        return self.document_repository.get_all_files()

    def get_all_files_from_mongo(self):
        return self.get_all_files()
