import tempfile
import zipfile
from pathlib import Path
from typing import List
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from config.settings import settings
from dao.document_dao import DocumentDAO
from dto.schemas import DeleteDocumentResponse, DocumentListResponse


router = APIRouter(prefix="/api/rag")
document_dao: DocumentDAO | None = None


def _ensure_document_dao() -> DocumentDAO:
    if document_dao is None:
        raise HTTPException(status_code=500, detail="Document service not initialized")
    return document_dao


def check_file_size(file: UploadFile) -> None:
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > settings.MAX_FILE_SIZE:
        max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制。最大允许 {max_size_mb:.0f}MB，当前文件大小 {size / (1024 * 1024):.1f}MB",
        )


def _read_uploads(files: List[UploadFile]) -> List[dict]:
    file_dicts: List[dict] = []
    if len(files) == 1 and files[0].filename and files[0].filename.lower().endswith(".zip"):
        check_file_size(files[0])
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "upload.zip"
            zip_path.write_bytes(files[0].file.read())
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                total_size = sum(info.file_size for info in zip_ref.filelist)
                if total_size > settings.MAX_FILE_SIZE:
                    max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
                    raise HTTPException(
                        status_code=413,
                        detail=f"解压后的文件总大小超过限制。最大允许 {max_size_mb:.0f}MB，当前总大小 {total_size / (1024 * 1024):.1f}MB",
                    )
                for info in zip_ref.infolist():
                    if info.is_dir():
                        continue
                    path_parts = Path(info.filename).parts
                    if len(path_parts) > 2:
                        raise HTTPException(status_code=400, detail="暂不支持嵌套文件夹上传，请仅上传单层文件夹内的文件")
                    file_dicts.append(
                        {
                            "filename": path_parts[-1],
                            "file_content": zip_ref.read(info.filename),
                        }
                    )
    else:
        total_size = 0
        for file in files:
            check_file_size(file)
            content = file.file.read()
            total_size += len(content)
            if total_size > settings.MAX_FILE_SIZE:
                max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
                raise HTTPException(
                    status_code=413,
                    detail=f"文件总大小超过限制。最大允许 {max_size_mb:.0f}MB，当前总大小 {total_size / (1024 * 1024):.1f}MB",
                )
            file_dicts.append({"file_content": content, "filename": file.filename})
    return file_dicts


@router.post("/add_document_batch")
async def add_document_batch(course_name: str = Form(...), files: List[UploadFile] = File(...)):
    dao = _ensure_document_dao()
    file_dicts = _read_uploads(files)
    file_ids = [
        dao.save_file(file_dict["file_content"], file_dict["filename"], course_name)
        for file_dict in file_dicts
    ]
    return {"message": "Documents added successfully.", "file_ids": file_ids}


@router.post("/add_document_multimodal_batch")
async def add_document_multimodal_batch(course_name: str = Form(...), files: List[UploadFile] = File(...)):
    return await add_document_batch(course_name=course_name, files=files)


@router.delete("/delete_document/{file_id}", response_model=DeleteDocumentResponse)
async def delete_document(file_id: str):
    dao = _ensure_document_dao()
    if not dao.delete_file(file_id):
        raise HTTPException(status_code=404, detail="文件不存在")
    return DeleteDocumentResponse(success=True, message="文件删除成功", file_id=file_id)


@router.get("/documents", response_model=DocumentListResponse)
async def get_documents(
    course_name: str = Query(..., description="课程名称"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    dao = _ensure_document_dao()
    documents, total = dao.get_documents_by_course(course_name, page, size)
    return {"documents": documents, "total": total}


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    dao = _ensure_document_dao()
    try:
        stream = dao.get_file_stream(file_id)
        filename = getattr(stream, "filename", "downloaded_file")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")

    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"}
    return StreamingResponse(stream, media_type="application/octet-stream", headers=headers)


@router.get("/preview/{file_id}")
async def preview_file(file_id: str):
    dao = _ensure_document_dao()
    try:
        stream = dao.get_file_stream(file_id)
        filename = getattr(stream, "filename", "preview.pdf")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")

    if not filename.lower().endswith(".pdf"):
        stream.close()
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件预览")

    headers = {"Content-Disposition": f"inline; filename*=UTF-8''{quote(filename)}"}
    return StreamingResponse(stream, media_type="application/pdf", headers=headers)
