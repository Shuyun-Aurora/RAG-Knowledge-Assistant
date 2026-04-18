from typing import List, Optional

from pydantic import BaseModel


class DeleteDocumentResponse(BaseModel):
    success: bool
    message: str
    file_id: Optional[str] = None
    warning: Optional[str] = None
    error: Optional[str] = None


class DocumentInfo(BaseModel):
    file_id: str
    filename: str
    course: str
    upload_time: Optional[str] = None
    size: Optional[int] = None


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total: int
