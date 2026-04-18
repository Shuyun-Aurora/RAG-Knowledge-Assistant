import {getJson, get, del, postFormData, PREFIX} from './common'; // 引入你封装的 postFormData

export async function uploadFile(fileList, courseName) {
    const formData = new FormData();
    formData.append('course_name', courseName);

    fileList.forEach((file) => {
        formData.append('files', file); // 注意字段是 files（后端要求）
    });

    return await postFormData(`${PREFIX}/rag/add_document_batch`, formData);
}

export async function uploadMultimodalFiles(fileList, courseName, parseMethod = 'auto') {
    const formData = new FormData();
    formData.append('course_name', courseName);
    formData.append('parse_method', parseMethod);

    fileList.forEach((file) => {
        formData.append('files', file); // 注意字段是 files（后端要求）
    });

    return await postFormData(`${PREFIX}/rag/add_document_multimodal_batch`, formData);
}

export async function deleteDocument(fileId) {
    return await del(`${PREFIX}/rag/delete_document/${fileId}`);
}

export async function getDocumentsByCourse(courseName, page = 1, size = 10) {
    const query = new URLSearchParams({
        course_name: courseName,
        page: page.toString(),
        size: size.toString()
    });
    return await getJson(`${PREFIX}/rag/documents?${query.toString()}`);
}

export async function downloadDocument(fileId, filename) {
    const url = `${PREFIX}/rag/download/${fileId}`;

    console.log('开始请求下载:', url);
    const res = await get(url);
    console.log('响应状态:', res.status, res.ok);

    if (!res.ok) {
        throw new Error('下载失败');
    }

    const blob = await res.blob();
    console.log('获取到blob:', blob);

    // 创建临时链接触发下载
    const downloadUrl = window.URL.createObjectURL(blob);
    console.log('创建下载链接:', downloadUrl);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename || 'downloaded_file';
    document.body.appendChild(a);
    console.log('准备触发点击下载');
    a.click();

    // 清理
    a.remove();
    window.URL.revokeObjectURL(downloadUrl);
    console.log('下载链接释放完成');
}

