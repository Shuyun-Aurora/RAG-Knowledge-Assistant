import React, {useContext, useEffect, useState} from 'react';
import UploadMaterial from '../components/UploadMaterial';
import UserContext from '../contexts/UserContext';
import CourseContext from "../contexts/CourseContext";
import MaterialList from "../components/MaterialList";
import MaterialPreview from "../components/MaterialPreview";
import useMessage from "antd/es/message/useMessage";
import {deleteDocument, getDocumentsByCourse} from "../service/file";
import { BASEURL } from "../service/common";
import NeumorphicPagination from "../components/NeumorphicPagination";
import { Modal } from 'antd';

const CourseMaterialsPage = () => {
    const user = useContext(UserContext);
    const isTeacher = user.role === 'teacher';
    const { course } = useContext(CourseContext);
    const [materials, setMaterials] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [size] = useState(4); // 每页大小固定

    const [loading, setLoading] = useState(false);
    const [previewVisible, setPreviewVisible] = useState(false);
    const [previewFile, setPreviewFile] = useState(null);
    const [messageApi, contextHolder] = useMessage();

    const fetchMaterials = async (pageNum = 1) => {
        if (!course?.name) return;
        setLoading(true);
        try {
            const res = await getDocumentsByCourse(course.name, pageNum, size);
            setMaterials(res.documents);
            setTotal(res.total);
            setPage(pageNum);
        } catch (e) {
            messageApi.error("获取资料失败");
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMaterials(1);
    }, [course?.name]);

    const onPageChange = (pageNum) => {
        fetchMaterials(pageNum);
    };

    const handleUpload = () => {
        fetchMaterials();  // 上传成功刷新列表
    };

    const handleDelete = async (item) => {
        try {
            const res = await deleteDocument(item.file_id);
            if (res.success) {
                messageApi.success("删除成功");
                // 重新获取当前页数据
                fetchMaterials(page);
            } else {
                messageApi.error(res.message || "删除失败");
            }
        } catch (err) {
            console.error(err);
            messageApi.error("删除出错，请稍后重试");
        }
    };

    // 资料预览逻辑
    const handlePreview = (file) => {
        setPreviewFile(file);
        setPreviewVisible(true);
    };
    const handlePreviewClose = () => {
        setPreviewVisible(false);
        setPreviewFile(null);
    };

    return (
        <>
            {contextHolder}
            {isTeacher && (
                <UploadMaterial
                    materials={materials}
                    onUpload={handleUpload}
                />
            )}
            <MaterialList
                materials={materials}
                loading={loading}
                isTeacher={isTeacher}
                onDelete={handleDelete}
                onPreview={handlePreview}
            />
            <Modal
                className="neumorphic-modal"
                open={previewVisible}
                title={previewFile?.filename}
                footer={null}
                onCancel={handlePreviewClose}
                width={800}
                styles={{ body: { minHeight: 500, padding: 0 } }}
                forceRender
            >
                {previewFile?.file_id && (
                    <iframe
                        key={previewFile.file_id}
                        src={`${BASEURL}/api/rag/preview/${previewFile.file_id}`}
                        style={{ width: '100%', height: '80vh', border: 'none' }}
                        title="课件预览"
                    />
                )}
            </Modal>
            
            <NeumorphicPagination 
                current={page} 
                total={total} 
                pageSize={size} 
                onChange={onPageChange} 
            />
        </>
    );
};

export default CourseMaterialsPage;
