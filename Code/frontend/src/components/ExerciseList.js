import React, {useContext} from 'react';
import {List, Card, Space, Typography, Button, Popconfirm} from 'antd';
import {useNavigate} from "react-router-dom";
import CourseContext from "../contexts/CourseContext";
import {DeleteOutlined, EyeOutlined, FileTextOutlined} from "@ant-design/icons";
import useMessage from "antd/es/message/useMessage";
import NeumorphicPagination from '../components/NeumorphicPagination';
import '../css/neumorphism.css';

const { Text } = Typography;

const ExerciseList = ({
    exercises,
    isTeacher = false,
    total = 0,
    pageSize = 10,
    onPageChange = () => {},
    current = 1,
    onDelete = () => {},
}) => {
    const navigate = useNavigate();
    const {courseId} = useContext(CourseContext);
    const [messageApi, contextHolder] = useMessage();

    const confirmDelete = async (item) => {
        try {
            await onDelete(item);
            messageApi.success('删除成功');
        } catch (e) {
            console.error(e);
            messageApi.error('删除失败');
        }
    };

    return (
        <>
            {contextHolder}
            <List
                dataSource={exercises}
                pagination={false}
                renderItem={(item, idx) => (
                    <List.Item style={{ padding: 0, border: 'none', background: 'transparent' }}>
                        <Card size="small" className="course-card material-card" style={{ width: '100%', marginBottom: 20, background: idx % 2 === 0 ? 'rgba(200, 227, 246, 0.6)' : 'rgba(154, 197, 230, 0.6)', cursor: 'pointer', border: 'none', padding: 0 }} onClick={() => navigate(`/course/${courseId}/exercises/${item.id}`)}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                {/* 左侧图标+文字，图标垂直居中 */}
                                <div style={{ display: 'flex', alignItems: 'center', maxWidth: 500 }}>
                                    <FileTextOutlined style={{ fontSize: 20, color: '#aaa', marginRight: 12 }} />
                                    <div style={{ whiteSpace: 'normal' }}>
                                        <Text strong>{item.title}</Text>
                                        <br />
                                        <Text type="secondary" style={{ maxWidth: 400, whiteSpace: 'normal' }}>
                                            {item.description || '暂无描述'}
                                        </Text>
                                    </div>
                                </div>
                                {/* 右侧按钮组 */}
                                <Space size="small" align="center" onClick={e => e.stopPropagation()}>
                                    <Button 
                                            className="coursecard-btn coursecard-btn-dissolve"
                                            size="middle"
                                            icon={<EyeOutlined />}
                                        onClick={() => navigate(`/course/${courseId}/exercises/${item.id}`)}
                                            style={{ minWidth: 60, background: idx % 2 === 0 ? 'rgba(200, 227, 246, 0.6)' : 'rgba(154, 197, 230, 0.6)' }}
                                    >
                                    查看
                                    </Button>
                                    {isTeacher && (
                                        <Popconfirm
                                            title="确定删除该习题集吗？"
                                            okText="删除"
                                            cancelText="取消"
                                            onConfirm={() => confirmDelete(item)}
                                        >
                                            <Button 
                                                className="coursecard-btn coursecard-btn-danger"
                                                size="middle"
                                                icon={<DeleteOutlined />}
                                                onClick={e => e.stopPropagation()}
                                                style={{ minWidth: 60, background: idx % 2 === 0 ? 'rgba(200, 227, 246, 0.6)' : 'rgba(154, 197, 230, 0.6)' }}
                                            >
                                                删除
                                            </Button>
                                        </Popconfirm>
                                    )}
                                </Space>
                            </div>
                        </Card>
                    </List.Item>
                )}
            />
            
            {/* 添加自定义拟态分页器 */}
            {total > 0 && (
                <NeumorphicPagination 
                    current={current} 
                    total={total} 
                    pageSize={pageSize} 
                    onChange={onPageChange} 
                />
            )}
        </>
    );
};

export default ExerciseList;