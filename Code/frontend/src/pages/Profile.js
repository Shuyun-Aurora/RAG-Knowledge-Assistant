import React, {useContext, useEffect, useState} from 'react';
import {Card, Button, Typography, Layout, Avatar, Divider, Row, Col, Statistic, Form, Modal, Input, Spin} from 'antd';
import { useNavigate } from 'react-router-dom';
import { UserOutlined, BookOutlined, LogoutOutlined } from '@ant-design/icons';
import { TrophyOutlined, SmileOutlined } from '@ant-design/icons';
import AppHeader from '../components/Header';
import { logout } from '../service/login';
import 'antd/dist/reset.css';
import useMessage from "antd/es/message/useMessage";
import UserContext from "../contexts/UserContext";
import {changePassword, getUserCourseCount, updateProfile} from "../service/user";
import {getJoinedCourses, getTaughtCourses} from "../service/course";
import '../css/coursecard.css';

const { Content } = Layout;
const { Title, Text } = Typography;

const Profile = () => {
  const navigate = useNavigate();
  const [messageApi, contextHolder] = useMessage();

  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editForm] = Form.useForm();

  const user = useContext(UserContext);
  const [courseCount, setCourseCount] = useState(null);
  const [loadingStats, setLoadingStats] = useState(true);

  const getStageByCourseCount = (count, role) => {
    if (role === 'teacher') {
      if (count === 0) return { name: '初露锋芒', desc: '还没有开设课程，快来创建吧！', emoji: '🧑‍🏫' };
      if (count <= 3) return { name: '经验积累', desc: '已有课程进行中，继续丰富教学经验~', emoji: '📚' };
      return { name: '教学专家', desc: '教学经验丰富，广受学生欢迎！', emoji: '🏆' };
    } else {
      if (count === 0) return { name: '新手起步', desc: '快来选第一门课程吧！', emoji: '🌱' };
      if (count <= 3) return { name: '稳步成长', desc: '学习进行中，加油！', emoji: '🚀' };
      return { name: '高手进阶', desc: '学习达人，继续冲！', emoji: '🎯' };
    }
  };

  useEffect(() => {
    async function fetchCourseCount() {
      try {
        const res = await getUserCourseCount();
        if (res?.success) {
          setCourseCount(res.courseCount);
        } else {
          console.error('获取课程数失败:', res?.message);
          setCourseCount(0);
        }
      } catch (e) {
        console.error('获取课程数失败', e);
        setCourseCount(0);
      } finally {
        setLoadingStats(false);
      }
    }
    fetchCourseCount();
  }, []);

  const handleLogout = () => {
    logout();
    messageApi.success('已退出登录');
    navigate('/login');
  };

  const openPasswordModal = () => {
    form.resetFields();
    setPasswordModalVisible(true);
  };

  const closePasswordModal = () => {
    setPasswordModalVisible(false);
  };

  const onPasswordFinish = async (values) => {
    const { oldPassword, newPassword, confirmPassword } = values;

    if (newPassword !== confirmPassword) {
      messageApi.error('两次输入的新密码不一致');
      return;
    }

    try {
      const res = await changePassword(oldPassword, newPassword);
      if (res.success) {
        messageApi.success('密码修改成功');
        closePasswordModal();
      } else {
        messageApi.error(res.message || '修改密码失败');
      }
    } catch (error) {
      messageApi.error('修改密码异常');
      console.error(error);
    }
  };

  // 打开/关闭编辑资料 Modal
  const openEditModal = () => {
    editForm.setFieldsValue({
      name: user.name,
      email: user.email
    });
    setEditModalVisible(true);
  };

  const closeEditModal = () => {
    setEditModalVisible(false);
  };

// 提交编辑资料
  const onEditFinish = async (values) => {
    try {
      const res = await updateProfile(values);
      if (res.success) {
        messageApi.success('资料更新成功');
        closeEditModal();
        window.location.reload(); // 手动更新 context
      } else {
        messageApi.error(res.message || '资料更新失败');
      }
    } catch (e) {
      messageApi.error('请求失败');
      console.error(e);
    }
  };

  const stage = getStageByCourseCount(courseCount || 0, user.role);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader 
        title="个人中心"
      />
      {contextHolder}
      <Content style={{ padding: '24px', background: 'transparent' }}>
        <div style={{ 
          maxWidth: 800, 
          margin: '0 auto', 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '24px' 
        }}>
          {/* 用户信息卡片 */}
          <Card className='neumorphic-card'>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', marginBottom: 24, width: '100%' }}>
              <Avatar 
                size={80}
                style={{ 
                  marginBottom: 0, 
                  fontSize: 48, 
                  background: '#f0f4fa', 
                  color: '#333', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  lineHeight: '80px',
                  textAlign: 'center',
                  padding: 0
                }}
              >
                <span style={{
                  display: 'inline-block',
                  width: '100%',
                  lineHeight: '80px',
                  textAlign: 'center',
                  fontSize: 48
                }}>{user.role === 'teacher' ? '🧑‍🏫' : '🧑‍🎓'}</span>
              </Avatar>
              <Title level={2} style={{ margin: '8px 0' }}>{user.username}</Title>
            </div>
            
            <Divider style={{ borderColor: '#E6E6FA' }} />

            <Row gutter={24}>
              <Col span={12}>
                <div style={{ marginBottom: 16 }}>
                  <Text strong>姓名：</Text>
                  <Text>{user.name || '未填写'}</Text>
                </div>
                <div style={{ marginBottom: -4 }}>
                  <Text strong>邮箱：</Text>
                  <Text>{user.email || '未填写'}</Text>
                </div>
              </Col>
              <Col span={12}>
                <div style={{ marginBottom: 16 }}>
                  <Text strong>身份：</Text>
                  <Text>{user.role === 'teacher' ? '教师' : '学生'}</Text>
                </div>
                <div style={{ marginBottom: -4}}>
                  <Text strong>登录状态：</Text>
                  <Text>已登录</Text>
                </div>
              </Col>
            </Row>
          </Card>

          {/* 课程统计信息卡 */}
          <Row gutter={24} style={{ marginTop: 8 }}>
            {[{
              icon: <BookOutlined style={{ fontSize: 36, color: '#7bb1d1' , marginBottom: 8 }} />,
              title: <Text style={{ fontSize: 18, fontWeight: 'normal' }}>
                {user.role === 'teacher' ? '开设课程' : '参与课程'}：{courseCount}
              </Text>,
            }, {
              icon: <TrophyOutlined style={{ fontSize: 36, color: '#fbe7d6', marginBottom: 8 }} />,
              title: <Text style={{ fontSize: 18, fontWeight: 'normal' }}>{stage.name}</Text>,
            }, {
              icon: <SmileOutlined style={{ fontSize: 36, color: '#9aaaa3', marginBottom: 8 }} />,
              title: <Text style={{ fontSize: 18, fontWeight: 'normal' }}>{stage.desc}</Text>,
            }].map(({ icon, title, content }, idx) => (
                <Col span={8} key={idx}>
                  <div className="card-wrap">
                    <div
                      className="course-card"
                      style={{
                        background: idx % 2 === 0 ? 'rgba(200, 227, 246, 0.6)' : 'rgba(154, 197, 230, 0.6)',
                        width: '100%',
                        height: 160,
                        minHeight: 160,
                        margin: '0 auto',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center',
                      }}
                    >
                      <div style={{
                        flex: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center',
                        width: '100%',
                        padding: '0 32px',
                      }}>
                        {icon}
                        {title && <Title level={4} style={{ marginBottom: 4 }}>{title}</Title>}
                        {content}
                      </div>
                    </div>
                  </div>
                </Col>
            ))}
          </Row>

          {/* 操作按钮 */}
          <Card
            className='neumorphic-card'>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between',
              gap: 16
            }}>
              <Title level={4} style={{ margin: 0 }}>账号操作</Title>
              <div style={{ 
                display: 'flex', 
                gap: 16, 
                maxWidth: 500
              }}>
                <Button 
                  className='neumorphic-btn'
                  type="primary" 
                  size="large"
                  onClick={openEditModal}
                >
                  编辑资料
                </Button>
                <Button 
                  className='neumorphic-btn'
                  size="large"
                  onClick={openPasswordModal}
                >
                  修改密码
                </Button>
                <Button 
                  className='neumorphic-btn'
                  type="primary" 
                  danger 
                  icon={<LogoutOutlined />} 
                  size="large"
                  onClick={handleLogout}
                >
                  退出登录
                </Button>
              </div>
            </div>
          </Card>

          {/* 修改密码弹窗 */}
          <Modal
              className="neumorphic-modal"
              title="修改密码"
              visible={passwordModalVisible}
              onCancel={closePasswordModal}
              onOk={() => form.submit()}
              okText="提交"
          >
            <Form form={form} layout="vertical" onFinish={onPasswordFinish}>
              <Form.Item
                  label="旧密码"
                  name="oldPassword"
                  rules={[{ required: true, message: '请输入旧密码' }]}
              >
                <Input.Password />
              </Form.Item>
              <Form.Item
                  label="新密码"
                  name="newPassword"
                  rules={[{ required: true, message: '请输入新密码' }]}
              >
                <Input.Password />
              </Form.Item>
              <Form.Item
                  label="确认新密码"
                  name="confirmPassword"
                  rules={[{ required: true, message: '请确认新密码' }]}
              >
                <Input.Password />
              </Form.Item>
            </Form>
          </Modal>

          {/* 编辑资料弹窗 */}
          <Modal
              className="neumorphic-modal"
              title="编辑资料"
              visible={editModalVisible}
              onCancel={closeEditModal}
              onOk={() => editForm.submit()}
              okText="提交"
          >
            <Form form={editForm} layout="vertical" onFinish={onEditFinish}>
              <Form.Item
                  label="姓名"
                  name="name"
                  rules={[{ required: true, message: '请输入姓名' }]}
              >
                <Input />
              </Form.Item>
              <Form.Item
                  label="邮箱"
                  name="email"
                  rules={[
                    { required: true, message: '请输入邮箱' },
                    { type: 'email', message: '邮箱格式不正确' }
                  ]}
              >
                <Input />
              </Form.Item>
            </Form>
          </Modal>
        </div>
      </Content>
    </Layout>
  );
};

export default Profile; 