from typing import Any, Dict, Optional

import gridfs
from bson import ObjectId
from pymongo import MongoClient
from config.settings import settings


class DocumentRepository:
    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URI)
        # Keep the document storage database aligned with the original main branch behavior.
        self.db = self.client["rag"]
        self.fs = gridfs.GridFS(self.db)

    def save_file(self, file_content: bytes, filename: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        file_id = self.fs.put(file_content, filename=filename, metadata=metadata or {})
        return str(file_id)

    def get_documents_by_course(self, course_name: str, page: int, size: int) -> Dict[str, Any]:
        query = {"metadata.course": course_name}
        total = self.db.fs.files.count_documents(query)
        skip = (page - 1) * size
        cursor = self.db.fs.files.find(query).skip(skip).limit(size).sort("uploadDate", -1)
        return {"items": list(cursor), "total": total}

    def get_file_stream(self, file_id: str):
        return self.fs.get(ObjectId(file_id))

    def delete_file(self, file_id: str) -> bool:
        try:
            self.fs.delete(ObjectId(file_id))
            return True
        except Exception:
            return False

    def close(self) -> None:
        self.client.close()
