import React, { useContext, useState } from 'react';
import { Card, Upload, Button, Typography, Spin } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import courseContext from "../contexts/CourseContext";
import { uploadFile } from "../service/file";
import useMessage from "antd/es/message/useMessage";
import { MAX_FILE_SIZE } from "../config/settings";
import "../css/global.css";

const { Text } = Typography;

const UploadMaterial = ({ materials = [], onUpload }) => {
    const [uploading, setUploading] = useState(false);
    const [fileList, setFileList] = useState([]);
    const [messageApi, contextHolder] = useMessage();

    const { course } = useContext(courseContext);
    const courseName = course?.name;

    if (!courseName) {
        return (
            <>
                {contextHolder}
                <Spin tip="课程信息加载中..." />
            </>
        );
    }

    const handleChange = ({ fileList }) => {
        setFileList(fileList);
    };

    const handleUpload = async () => {
        if (fileList.length === 0) {
            messageApi.warning("请先选择文件");
            return;
        }

        setUploading(true);
        try {
            const files = fileList.map((file) => file.originFileObj);
            const totalSize = files.reduce((sum, file) => sum + file.size, 0);

            if (totalSize > MAX_FILE_SIZE) {
                messageApi.error(`文件总大小(${(totalSize / 1024 / 1024).toFixed(1)}MB)超过限制${MAX_FILE_SIZE / 1024 / 1024}MB，请重新上传`);
                return;
            }

            await uploadFile(files, courseName);
            messageApi.success("文件上传成功");
            onUpload();
            setFileList([]);
        } catch (error) {
            if (error.response && error.response.status === 413) {
                messageApi.error(error.response.data.detail || `文件大小超过限制${MAX_FILE_SIZE / 1024 / 1024}MB，请重新上传`);
            } else {
                messageApi.error("上传失败");
                console.error(error);
            }
        } finally {
            setUploading(false);
        }
    };

    return (
        <Card
            className="neumorphic-card"
            title="上传课程资料"
            style={{ marginBottom: 24 }}
            extra={<Text type="secondary">已上传 {materials.length} 个文件</Text>}
        >
            {contextHolder}
            <div style={{ marginBottom: 16 }}>
                <Upload
                    multiple
                    fileList={fileList}
                    onChange={handleChange}
                    beforeUpload={() => false}
                >
                    <Button className="neumorphic-btn" icon={<UploadOutlined />} size="large">
                        选择文件
                    </Button>
                </Upload>
            </div>

            <Typography.Paragraph type="secondary">
                支持上传：
                <ul style={{ paddingLeft: 20 }}>
                    <li>单个文件，如 Word、PDF、PPT、TXT 等</li>
                    <li>多个文件批量上传</li>
                    <li>ZIP 压缩包，后端会自动解压单层目录中的文件</li>
                </ul>
                <Text type="danger">注意：</Text>
                <ul style={{ paddingLeft: 20 }}>
                    <li>暂不支持 ZIP 中嵌套多层文件夹</li>
                    <li>单个文件或文件总大小不能超过 {MAX_FILE_SIZE / 1024 / 1024}MB</li>
                </ul>
            </Typography.Paragraph>

            <Button
                type="primary"
                className="neumorphic-btn"
                onClick={handleUpload}
                disabled={fileList.length === 0}
                loading={uploading}
                style={{ marginTop: 16 }}
            >
                {uploading ? "上传中..." : "开始上传"}
            </Button>
        </Card>
    );
};

export default UploadMaterial;
