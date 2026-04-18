import json
import shutil
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, BinaryIO, Dict, List, Optional
from uuid import uuid4

from config.settings import settings


class DocumentRepository:
    def __init__(self, upload_dir: Optional[str] = None):
        self.base_dir = Path(upload_dir or settings.UPLOAD_DIR)
        self.files_dir = self.base_dir / "files"
        self.index_path = self.base_dir / "index.json"
        self._lock = Lock()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self._write_index({})

    def save_file(self, file_content: bytes, filename: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        file_id = uuid4().hex
        stored_name = f"{file_id}_{Path(filename).name}"
        file_path = self.files_dir / stored_name
        file_path.write_bytes(file_content)

        record = {
            "file_id": file_id,
            "filename": Path(filename).name,
            "stored_name": stored_name,
            "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": metadata or {},
            "size": len(file_content),
        }

        with self._lock:
            index = self._read_index()
            index[file_id] = record
            self._write_index(index)
        return file_id

    def get_documents_by_course(self, course_name: str, page: int, size: int) -> Dict[str, Any]:
        index = self._read_index()
        matched = [
            record
            for record in index.values()
            if record.get("metadata", {}).get("course") == course_name
        ]
        matched.sort(key=lambda item: item.get("upload_time", ""), reverse=True)

        start = (page - 1) * size
        end = start + size
        return {"items": matched[start:end], "total": len(matched)}

    def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        index = self._read_index()
        record = index.get(file_id)
        if not record:
            return None
        file_path = self.files_dir / record["stored_name"]
        if not file_path.exists():
            return None
        return {
            "file_id": record["file_id"],
            "filename": record["filename"],
            "size": record.get("size", 0),
            "upload_time": record.get("upload_time"),
            "metadata": record.get("metadata", {}),
            "path": str(file_path),
        }

    def get_file_stream(self, file_id: str) -> BinaryIO:
        file_info = self.get_file(file_id)
        if not file_info:
            raise FileNotFoundError(file_id)
        stream = open(file_info["path"], "rb")
        setattr(stream, "filename", file_info["filename"])
        return stream

    def delete_file(self, file_id: str) -> bool:
        with self._lock:
            index = self._read_index()
            record = index.pop(file_id, None)
            if not record:
                return False
            self._write_index(index)

        file_path = self.files_dir / record["stored_name"]
        if file_path.exists():
            file_path.unlink()
        return True

    def get_all_files(self) -> List[Dict[str, Any]]:
        return list(self._read_index().values())

    def close(self) -> None:
        return None

    def clear(self) -> None:
        with self._lock:
            self._write_index({})
        if self.files_dir.exists():
            shutil.rmtree(self.files_dir)
        self.files_dir.mkdir(parents=True, exist_ok=True)

    def _read_index(self) -> Dict[str, Any]:
        if not self.index_path.exists():
            return {}
        return json.loads(self.index_path.read_text(encoding="utf-8") or "{}")

    def _write_index(self, index: Dict[str, Any]) -> None:
        self.index_path.write_text(
            json.dumps(index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
