import React, { useContext, useEffect, useState } from 'react';
import { Card, Typography, Button, InputNumber, Select } from 'antd';
import QAChat from '../components/QAChat';
import MaterialPreview from '../components/MaterialPreview';
import { qaHistory } from '../data/mockData';
import UserContext from '../contexts/UserContext';
import CourseContext from "../contexts/CourseContext";
import { getDocumentsByCourse } from '../service/file';
import { useSearchParams } from 'react-router-dom';

const { Text } = Typography;

const CourseQAPage = () => {
  const { courseId, course } = useContext(CourseContext);
  const user = useContext(UserContext);
  const fullQaHistory = qaHistory[courseId] || [];
  const userQaHistory = [];
  const [searchParams] = useSearchParams();
  const urlSessionId = searchParams.get('session_id');

  // 历史处理逻辑不变
  if (user) {
    for (let i = 0; i < fullQaHistory.length; i++) {
      const message = fullQaHistory[i];
      if (message.type === 'question' && message.user === user.name) {
        userQaHistory.push({ ...message, user: '我' });
        if (i + 1 < fullQaHistory.length && fullQaHistory[i + 1].type === 'answer') {
          userQaHistory.push(fullQaHistory[i + 1]);
          i++;
        }
      }
    }
  }

  // 课件相关状态
  const [materials, setMaterials] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedPage, setSelectedPage] = useState(null);
  const [loading, setLoading] = useState(false);

  // 获取课件
  useEffect(() => {
    if (!course?.name) return;
    setLoading(true);
    getDocumentsByCourse(course.name, 1, 100)
      .then(res => {
        setMaterials(res.documents || []);
      })
      .finally(() => setLoading(false));
  }, [course?.name]);

  // 课件单选
  const handleFileSelect = (fileId, checked) => {
    setSelectedFile(checked ? fileId : null);
    setSelectedPage(null); // 切换课件时清空页码
  };

  // 选择页码
  const handlePageChange = (value) => {
    setSelectedPage(value);
  };

  // 引用选择区，传递给 QAChat
  const referenceBar = (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: 12,
      padding: '0',
      marginBottom: 12,
      borderBottom: 'none', // 去掉分界线
      minHeight: 40 // 保证和输入框高度一致
    }}>
      <Select
        allowClear
        style={{ minWidth: 180, height: 40, display: 'flex', alignItems: 'center' }}
        placeholder="选择引用课件（单选）"
        value={selectedFile}
        onChange={setSelectedFile}
        size="middle"
        dropdownStyle={{ fontSize: 15 }}
      >
        {materials.map(item => (
          <Select.Option key={item.file_id} value={item.file_id}>
            {item.filename}
          </Select.Option>
        ))}
      </Select>
      <InputNumber
        className="neumorphic-input-number"
        min={1}
        placeholder="页码（可选）"
        value={selectedPage}
        onChange={handlePageChange}
        style={{ width: 120, height: 40, display: 'flex', alignItems: 'center' }}
        disabled={!selectedFile}
        size="middle"
      />
    </div>
  );

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      {/* 左侧课件区 */}
      {materials.length > 0 ? (
        <div style={{ borderRight: '1px solid #eee', padding: 16, overflowY: 'auto', minWidth: 400, maxWidth: 400, width: 400 }}>
          <MaterialPreview
            materials={materials}
            loading={loading}
            selectedFile={selectedFile}
            onFileSelect={handleFileSelect}
            onPreview={(file) => console.log('Preview:', file)}
          />
        </div>
      ) : (
        <div style={{ borderRight: '1px solid #eee', padding: 16, overflowY: 'auto', minWidth: 400, maxWidth: 400, width: 400 }}>
          <div className="neumorphic-card" style={{
            width: '100%',
            minHeight: 180,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#888',
            fontSize: 18,
            boxShadow: '0 4px 24px 0 rgba(154,197,230,0.18), 0 1.5px 4px 0 rgba(135,169,193,0.12)'
          }}>
            暂无课程资料
          </div>
        </div>
      )}
      {/* 右侧问答区 */}
      <div style={{padding: 16, flex: 1, minWidth: 0}}>
        <Card
          className="neumorphic-card" 
          title="智能问答"
          extra={<Text type="secondary">AI 助教为您解答课程相关问题</Text>}
          style={{ flex: 1,  minWidth: 0 }}
        >
          <QAChat
            initialHistory={userQaHistory}
            sessionId={urlSessionId}
            filename={materials.find(m => m.file_id === selectedFile)?.filename || null}
            pageNumber={selectedPage}
            referenceBar={referenceBar}
            courseName={course?.name}
          />
        </Card>
      </div>
    </div>
  );
};

export default CourseQAPage;