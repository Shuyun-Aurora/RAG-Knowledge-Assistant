import React from 'react';
import { List, Card, Space, Button, Typography } from 'antd';
import { FileTextOutlined, EyeOutlined, DownloadOutlined, DeleteOutlined } from '@ant-design/icons';
import {downloadDocument} from "../service/file";
import '../css/neumorphism.css';

const { Text } = Typography;

const MaterialList = ({ materials, loading = false, isTeacher = false, onDelete, onPreview }) => {
    function formatSize(bytes) {
        if (bytes === 0 || bytes == null) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    const handleDownload = async (item) => {
        try {
            await downloadDocument(item.file_id, item.filename);
        } catch (error) {
            console.error('下载失败:', error);
            alert('下载失败，请稍后重试');
        }
    };

    return (
    <List
        loading={loading}
      dataSource={materials}
      renderItem={(item, idx) => (
          <List.Item style={{ padding: 0, border: 'none', background: 'transparent' }}>
              <Card size="small" className="course-card material-card" style={{ width: '100%', marginBottom: 20, background: idx % 2 === 0 ? 'rgba(200, 227, 246, 0.6)' : 'rgba(154, 197, 230, 0.6)', cursor: 'pointer', border: 'none', padding: 0 }} onClick={() => onPreview && onPreview(item)}>
                  <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                  }}>
                      {/* 左侧图标+文字，图标垂直居中 */}
                      <div style={{ display: 'flex', alignItems: 'center', maxWidth: 500 }}>
                          <FileTextOutlined style={{ fontSize: 20, color: '#90a4ae', marginRight: 12 }} />
                          <div style={{ whiteSpace: 'normal' }}>
                              <Text strong>{item.filename}</Text>
                              <br />
                              <Text type="secondary">
                                  大小：{formatSize(item.size)} | 上传时间：{item.upload_time || '未知'}
                              </Text>
                          </div>
                      </div>

                      {/* 右侧按钮组 */}
                      <Space size="small" align="center" onClick={e => e.stopPropagation()}>
                          <Button
                              className="coursecard-btn coursecard-btn-dissolve"
                              icon={<DownloadOutlined />}
                              size="middle"
                              onClick={() => handleDownload(item)}
                              style={{ minWidth: 60, background: idx % 2 === 0 ? 'rgba(200, 227, 246, 0.6)' : 'rgba(154, 197, 230, 0.6)' }}
                          >
                              下载
                          </Button>
                          {isTeacher && (
                              <Button
                                  className="coursecard-btn coursecard-btn-danger"
                                  icon={<DeleteOutlined />}
                                  size="middle"
                                  onClick={() => onDelete && onDelete(item)}
                                  style={{ minWidth: 60, background: idx % 2 === 0 ? 'rgba(200, 227, 246, 0.6)' : 'rgba(154, 197, 230, 0.6)' }}
                              >
                                  删除
                              </Button>
                          )}
                      </Space>
                  </div>
              </Card>
          </List.Item>
      )}
    />
  );
};

export default MaterialList; 