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

    def get_documents_by_course(self, course_name: str, page: int, size: int):
        documents = self.document_repository.get_documents_by_course(course_name, page, size)
        result = []
        for doc in documents["items"]:
            result.append(
                {
                    "file_id": str(doc.get("_id", doc.get("file_id"))),
                    "filename": doc.get("filename"),
                    "upload_time": (
                        doc.get("upload_time")
                        or (doc.get("uploadDate").strftime("%Y-%m-%d %H:%M:%S") if doc.get("uploadDate") else None)
                    ),
                    "course": doc.get("metadata", {}).get("course"),
                    "size": doc.get("size", doc.get("length", 0)),
                }
            )
        return result, documents["total"]

    def get_file_stream(self, file_id: str):
        return self.document_repository.get_file_stream(file_id)

    def delete_file(self, file_id: str) -> bool:
        return self.document_repository.delete_file(file_id)
