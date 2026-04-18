import { getJson, get, del, postFormData, PREFIX } from './common';

export async function uploadFile(fileList, courseName) {
    const formData = new FormData();
    formData.append('course_name', courseName);

    fileList.forEach((file) => {
        formData.append('files', file);
    });

    return await postFormData(`${PREFIX}/rag/add_document_batch`, formData);
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
    const res = await get(url);

    if (!res.ok) {
        throw new Error('下载失败');
    }

    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = filename || 'downloaded_file';
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(downloadUrl);
}
