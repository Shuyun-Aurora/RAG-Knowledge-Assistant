from urllib.parse import quote

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Query, Depends
from fastapi.responses import StreamingResponse
from service.rag_service import RAGService
from dto.schemas import QueryRequest, DeleteDocumentResponse, DocumentListResponse, \
    StatisticsResponse, ChatHistorySummaryResponse, AgentStylesResponse
from service.UserService import get_current_user
from entity.User import User
import json
import asyncio
import uuid
from typing import List
import zipfile
import tempfile
from sqlalchemy.orm import Session
from entity.ExerciseSet import ExerciseSet
from config.db import get_db  # 修改这一行，从 config.db 导入而不是 service.db
from config.settings import settings


router = APIRouter(prefix="/api/rag")
rag_service: RAGService = None  # 将在 main.py 初始化后注入


def check_file_size(file: UploadFile):
    """检查文件大小是否超过限制"""
    # 获取文件大小
    file.file.seek(0, 2)  # 移动到文件末尾
    size = file.file.tell()  # 获取文件大小
    file.file.seek(0)  # 移动回文件开头
    
    if size > settings.MAX_FILE_SIZE:
        max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制。最大允许 {max_size_mb:.0f}MB，当前文件大小 {size/(1024*1024):.1f}MB"
        )


@router.post("/add_document_batch")
async def add_document_batch(
        course_name: str = Form(...),
        files: List[UploadFile] = File(...)
):
    file_dicts = []
    # 检查是否为单个zip压缩包
    if len(files) == 1 and files[0].filename.lower().endswith('.zip'):
        # 检查zip文件大小
        check_file_size(files[0])
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = f"{tmpdir}/upload.zip"
            with open(zip_path, "wb") as f:
                f.write(files[0].file.read())
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 检查解压后的所有文件总大小
                total_size = sum(info.file_size for info in zip_ref.filelist)
                if total_size > settings.MAX_FILE_SIZE:
                    max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
                    raise HTTPException(
                        status_code=413,
                        detail=f"解压后的文件总大小超过限制。最大允许 {max_size_mb:.0f}MB，当前总大小 {total_size/(1024*1024):.1f}MB"
                    )
                zip_ref.extractall(tmpdir)
                for name in zip_ref.namelist():
                    if name.endswith("/"):
                        # 只允许单层目录
                        if "/" in name.strip("/"):
                            raise HTTPException(status_code=400, detail="暂不支持嵌套文件夹上传，请仅上传单层文件夹内的文件")
                        continue
                    if "/" in name:
                        # 只允许一层文件夹
                        if len(name.strip("/").split("/")) > 2:
                            raise HTTPException(status_code=400, detail="暂不支持嵌套文件夹上传，请仅上传单层文件夹内的文件")
                    file_path = f"{tmpdir}/{name}"
                    with open(file_path, "rb") as f:
                        content = f.read()
                    file_dicts.append({"file_content": content, "filename": name})
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
                    detail=f"文件总大小超过限制。最大允许 {max_size_mb:.0f}MB，当前总大小 {total_size/(1024*1024):.1f}MB"
                )
            file_dicts.append({"file_content": content, "filename": file.filename})
    
    file_ids = rag_service.upload_document_batch(file_dicts, course_name)
    return {"message": "Documents added successfully.", "file_ids": file_ids}


@router.post("/add_document_multimodal")
async def add_document_with_mineru(
        file: UploadFile = File(...),
        course_name: str = Form(...),
        parse_method: str = Form("auto"),
        generate_knowledge_graph: bool = Form(True)
):
    """
    使用MinerU解析器上传文档，支持图片、表格、公式的视觉分析
    
    Args:
        file: 上传的文件
        course_name: 课程名称
        parse_method: 解析方法 ("auto", "ocr", "layout", "table")
        generate_knowledge_graph: 是否生成知识图谱（后台异步进行）
    """
    # 读取文件内容
    file_content = await file.read()

    # 通过Service层处理文件上传业务逻辑，使用MinerU解析
    file_id = await rag_service.upload_document_with_mineru(
        file_content=file_content, 
        filename=file.filename, 
        course_name=course_name,
        parse_method=parse_method,
        generate_knowledge_graph=generate_knowledge_graph
    )

    return {
        "message": "Document added successfully with MinerU parsing. Knowledge graph generation is running in background.",
        "file_id": file_id,
        "parse_method": parse_method,
        "knowledge_graph_status": "processing" if generate_knowledge_graph else "disabled"
    }


@router.post("/add_document_multimodal_batch")
async def add_document_multimodal_batch(
    course_name: str = Form(...),
    files: List[UploadFile] = File(...),
    parse_method: str = Form("auto"),
    generate_knowledge_graph: bool = Form(True)
):
    file_ids = []

    # 读取文件，保存 MongoDB 等
    for file in files:
        content = await file.read()
        file_id = rag_service.document_dao.save_file_to_mongo(content, file.filename, course_name)
        file_ids.append(file_id)
        # 提交到线程池后台处理
        rag_service.submit_multimodal_processing(
            content,
            file.filename,
            course_name,
            parse_method,
            file_id,
            generate_knowledge_graph,
        )

    return {
        "message": "Batch upload successful. Files are being processed in background.",
        "file_ids": file_ids,
        "parse_method": parse_method,
        "knowledge_graph_status": "processing" if generate_knowledge_graph else "disabled"
    }


@router.delete("/delete_document/{file_id}", response_model=DeleteDocumentResponse)
async def delete_document(file_id: str):
    """
    删除文档及其对应的向量（使用ChromaDB后，此操作很快）
    :param file_id: 文件ID
    :return: 删除结果
    """
    if not rag_service:
        raise HTTPException(status_code=500, detail="Service not initialized")

    # 直接调用服务层的方法，不再需要后台任务
    result = rag_service.delete_document(file_id)

    if result["success"]:
        return result
    else:
        # 可以根据result中的具体错误信息返回更详细的HTTPException
        raise HTTPException(status_code=400, detail=result.get("message", "删除失败"))


@router.get("/documents", response_model=DocumentListResponse)
async def get_documents(
    course_name: str = Query(..., description="课程名称"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    """
    按课程名称分页获取文档列表
    """
    if not rag_service:
        raise HTTPException(status_code=500, detail="Service not initialized")

    documents, total = rag_service.get_documents_by_course(course_name, page, size)
    return {"documents": documents, "total": total}


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    try:
        stream = rag_service.get_file_stream(file_id)  # 返回一个带有文件内容和文件名的流
        filename = getattr(stream, "filename", "downloaded_file")
        # 对文件名做URL编码，避免中文或空格问题
        quoted_filename = quote(filename)
    except Exception:
        raise HTTPException(status_code=404, detail="文件不存在或ID无效")

    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{quoted_filename}"
    }
    return StreamingResponse(stream, media_type="application/octet-stream", headers=headers)

@router.get("/preview/{file_id}")
async def preview_file(file_id: str):
    """
    PDF预览接口，支持前端iframe流式预览PDF文件
    :param file_id: 文件ID
    :return: PDF文件流
    """
    if not rag_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    try:
        stream = rag_service.get_file_stream(file_id)
        filename = getattr(stream, "filename", "preview.pdf")
        # 只允许PDF文件预览
        if not filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="仅支持PDF文件预览")
    except Exception:
        raise HTTPException(status_code=404, detail="文件不存在或ID无效")
    headers = {
        "Content-Disposition": f"inline; filename*=UTF-8''{quote(filename)}"
    }
    return StreamingResponse(stream, media_type="application/pdf", headers=headers)

@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """
    获取系统统计信息:vector和file数量，并返回所有file的id
    :return: 统计信息
    """
    if not rag_service:
        raise HTTPException(status_code=500, detail="Service not initialized")

    stats = rag_service.get_statistics()
    return stats


@router.get("/vector_info")
async def get_vector_info():
    """
    获取向量存储的详细信息
    :return: 向量信息
    """
    if not rag_service:
        raise HTTPException(status_code=500, detail="Service not initialized")

    vector_info = rag_service.get_vector_info()
    return vector_info


@router.post("/chat")
async def chat(request: Request, current_user: User = Depends(get_current_user)):
    """
    流式聊天接口，支持会话ID和SSE格式响应
    """
    if not rag_service:
        raise HTTPException(status_code=500, detail="Service not initialized")

    # 解析请求数据
    data = await request.json()
    question = data.get("question")
    course_name = data.get("course_name")
    filename = data.get("filename")
    page_number = data.get("page_number")
    style = data.get("agent_style")  # 新增风格参数
    if not question or not course_name:
        raise HTTPException(status_code=400, detail="Question and course_name are required")

    # 生成或使用提供的session_id，这个会用作追踪和管理用户与AI助教之间的对话会话的唯一标识符。系统会使用session_id获取历史对话记录来增强当前的对话
    # 每次打开新的聊天框，如果不提供之前的session_id，就会创建一个新的会话
    # 如果提供了之前的session_id，就会继续之前的对话
    session_id = data.get("session_id") or str(uuid.uuid4())


    async def generate():
        try:
            async for chunk in rag_service.stream_query(
                question, session_id, current_user.id, course_name=course_name, filename=filename, page_idx=page_number, style=style
            ):
                # 统一处理chunk为JSON格式
                if not isinstance(chunk, dict):
                    chunk = {"data": chunk}
                chunk["session_id"] = session_id  # 包含session_id在响应中
                data = json.dumps(chunk, ensure_ascii=False)
                yield f"data: {data}\n\n"
                await asyncio.sleep(0.01)  # 小延迟确保流畅传输
        except (asyncio.CancelledError, ConnectionResetError):
            # 客户端主动断开，及时退出
            print("前端已断开，停止生成回答")
            return
        except Exception as e:
            error_data = {"type": "error", "data": str(e), "session_id": session_id}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        finally:
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
            "X-Session-ID": session_id,  # 在header中也提供session_id
        }
    )


@router.get("/chat_history/{session_id}")
async def get_chat_history(session_id: str, current_user: User = Depends(get_current_user)):
    """
    获取指定会话ID的历史记录（仅限会话所有者）
    :param session_id: 会话ID
    :param current_user: 当前用户
    :return: 历史记录列表
    """
    if not rag_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    history = rag_service.get_chat_history(session_id, current_user.id)
    return {"session_id": session_id, "history": history}


@router.get("/chat_sessions")
async def get_user_sessions(current_user: User = Depends(get_current_user)):
    """
    获取当前用户的所有会话ID
    :param current_user: 当前用户
    :return: 会话ID列表
    """
    if not rag_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    sessions = rag_service.get_user_sessions(current_user.id)
    return {"sessions": sessions}


@router.delete("/chat_history/{session_id}")
async def delete_chat_session(session_id: str, current_user: User = Depends(get_current_user)):
    """
    删除指定会话（仅限会话所有者）
    :param session_id: 会话ID
    :param current_user: 当前用户
    :return: 删除结果
    """
    if not rag_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    success = rag_service.delete_session(session_id, current_user.id)
    if success:
        return {"message": "会话删除成功", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="会话不存在或无权限删除")

@router.post("/add_document_multimodal_batch")
async def add_document_multimodal_batch(
    course_name: str = Form(...),
    files: List[UploadFile] = File(...),
    parse_method: str = Form("auto"),
    generate_knowledge_graph: bool = Form(True)
):
    """
    支持批量上传文档或zip压缩包。若为zip，自动解压，遍历所有文件（不支持嵌套文件夹），并行处理。
    知识图谱生成在后台异步进行，不会阻塞接口响应。
    """
    file_dicts = []
    # 检查是否为单个zip压缩包
    if len(files) == 1 and files[0].filename.lower().endswith('.zip'):
        # 检查zip文件大小
        check_file_size(files[0])
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = f"{tmpdir}/upload.zip"
            with open(zip_path, "wb") as f:
                f.write(files[0].file.read())
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 检查解压后的所有文件总大小
                total_size = sum(info.file_size for info in zip_ref.filelist)
                if total_size > settings.MAX_FILE_SIZE:
                    max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
                    raise HTTPException(
                        status_code=413,
                        detail=f"解压后的文件总大小超过限制。最大允许 {max_size_mb:.0f}MB，当前总大小 {total_size/(1024*1024):.1f}MB"
                    )
                zip_ref.extractall(tmpdir)
                for name in zip_ref.namelist():
                    if name.endswith("/"):
                        # 只允许单层目录
                        if "/" in name.strip("/"):
                            raise HTTPException(status_code=400, detail="暂不支持嵌套文件夹上传，请仅上传单层文件夹内的文件")
                        continue
                    if "/" in name:
                        # 只允许一层文件夹
                        if len(name.strip("/").split("/")) > 2:
                            raise HTTPException(status_code=400, detail="暂不支持嵌套文件夹上传，请仅上传单层文件夹内的文件")
                    file_path = f"{tmpdir}/{name}"
                    with open(file_path, "rb") as f:
                        content = f.read()
                    file_dicts.append({"file_content": content, "filename": name})
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
                    detail=f"文件总大小超过限制。最大允许 {max_size_mb:.0f}MB，当前总大小 {total_size/(1024*1024):.1f}MB"
                )
            file_dicts.append({"file_content": content, "filename": file.filename})

    file_ids = await rag_service.upload_document_multimodal_batch(
        files=file_dicts,
        course_name=course_name,
        parse_method=parse_method,
        generate_knowledge_graph=generate_knowledge_graph
    )
    return {
        "message": "Documents added successfully with MinerU parsing. Knowledge graph generation is running in background.",
        "file_ids": file_ids
    }


@router.get("/chat_history_summary")
async def get_chat_history_summary(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, description="返回记录数量限制", ge=1, le=100),
    course_name: str = Query(None, description="课程名称，可选")
):
    """
    获取当前用户的历史记录摘要，按时间倒序排列
    :param current_user: 当前用户
    :param limit: 返回记录数量限制（1-100）
    :param course_name: 课程名称，如果提供则只返回该课程的历史记录
    :return: 历史记录摘要列表
    """
    if not rag_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    if course_name:
        summaries = rag_service.get_user_history_summary_by_course(current_user.id, course_name, limit)
    else:
        summaries = rag_service.get_user_history_summary(current_user.id, limit)
    
    # 转换MongoDB的ObjectId为字符串，并格式化时间
    formatted_summaries = []
    for summary in summaries:
        formatted_summary = {
            "session_id": summary["session_id"],
            "first_question": summary.get("first_question", "未知问题"),
            "created_at": summary.get("created_at", summary.get("updated_at")),
            "updated_at": summary.get("updated_at"),
            "course_name": summary.get("course_name"),
            "message_count": summary.get("message_count", 0)
        }
        formatted_summaries.append(formatted_summary)
    
    return ChatHistorySummaryResponse(
        summaries=formatted_summaries,
        total_count=len(formatted_summaries)
    )


@router.get("/user_courses")
async def get_user_courses(current_user: User = Depends(get_current_user)):
    """
    获取当前用户参与过的所有课程名称
    :param current_user: 当前用户
    :return: 课程名称列表
    """
    if not rag_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    courses = rag_service.get_user_courses(current_user.id)
    
    return {
        "success": True,
        "message": "用户课程列表获取成功",
        "data": {
            "courses": courses,
            "total_count": len(courses)
        }
    }
@router.get("/currentReference")
async def get_current_reference(
    current_user: User = Depends(get_current_user),
    course_name: str = Query(..., description="课程名称"),
    session_id: str = Query(..., description="当前会话ID"),
    limit: int = Query(50, description="返回记录数量限制", ge=1, le=100),
    db: Session = Depends(get_db)  # 添加数据库会话依赖
):

    if not rag_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    # 获取指定会话的完整历史记录
    session_history = rag_service.get_chat_history(session_id)
    
    # 用于存储所有涉及的资料ID
    reference_ids = set()
    
    # 遍历会话历史
    for message in session_history:
        if message.get("type") == "ai":
            message_data = message.get("data", {})
            sources = message_data.get("additional_kwargs", {}).get("sources", [])
            if sources:
                # 检查第一个source的课程名
                first_source_course = sources[0].get("metadata", {}).get("course")
                # 如果课程名不匹配，跳过这条消息
                if first_source_course != course_name:
                    continue
                
                # 如果课程名匹配，收集所有source ID
                for source in sources:
                    metadata = source.get("metadata", {})
                    if "source" in metadata:
                        reference_ids.add(metadata["source"])
    
    # 将set转换为list，并限制返回数量
    reference_list = list(reference_ids)[:limit]
    
    # 从MongoDB获取文件名
    references_with_filenames = []
    document_names = []  # 用于收集所有文档名称
    
    for ref_id in reference_list:
        file_info = rag_service.document_dao.get_file_from_mongo(ref_id)
        if file_info:
            filename = file_info.get("filename", "Unknown")
            document_names.append(filename)
            references_with_filenames.append({
                "id": ref_id,
                "filename": filename
            })
        else:
            references_with_filenames.append({
                "id": ref_id,
                "filename": "File not found"
            })
    
    # 获取所有相关的练习题
    from service.ExerciseService import get_exercises_by_document_names
    exercises = get_exercises_by_document_names(db, document_names)
    
    # 将练习题按文档名分组
    exercises_by_document = {}
    for exercise in exercises:
        # 获取该练习题所属的习题集
        exercise_set = db.query(ExerciseSet).filter(ExerciseSet.id == exercise["exercise_set_id"]).first()
        if exercise_set:
            doc_name = exercise_set.document_name
            if doc_name not in exercises_by_document:
                exercises_by_document[doc_name] = []
            exercises_by_document[doc_name].append(exercise)
    
    # 将练习题添加到对应的文档信息中
    for ref in references_with_filenames:
        ref["exercises"] = exercises_by_document.get(ref["filename"], [])
    
    return {
        "references": references_with_filenames,
        "total_count": len(references_with_filenames)
    }

    


@router.get("/chat/agent_styles", response_model=AgentStylesResponse)
async def get_agent_styles():
    """
    获取所有可用的agent风格
    :return: agent风格列表
    """
    if not rag_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    styles = rag_service.agent_service.get_all_agent_styles()
    return AgentStylesResponse(styles=styles)
