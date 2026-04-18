import React, { useState } from 'react';
import { Form, Input, Button, Typography, Card, Spin ,message} from 'antd';
import { useNavigate } from 'react-router-dom';
import { UserOutlined, LockOutlined, BookOutlined } from '@ant-design/icons';
import useMessage from "antd/es/message/useMessage";
import { login } from '../service/login';
import '../css/neumorphism.css';
import '../css/doghello.css';

const { Title, Text } = Typography;

const Login = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [messageApi, contextHolder] = useMessage();
  const [loading, setLoading] = useState(false);

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const result = await login(values.username, values.password);
      if (result?.success) {
        message.success(result.message || '登录成功');
        navigate('/');
      } else {
        message.error(result?.message || '登录失败');
      }
    } catch (error) {
      messageApi.error('网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-bg" style={{ 
      display: 'flex', 
      justifyContent: 'flex-end', 
      alignItems: 'center', 
      minHeight: '100vh', 
      position: 'relative',
      background: 'linear-gradient(to bottom, rgba(135, 169, 193, 0.6) 0%, #ccf6ff 60%, #fff 100%)'
    }}>
      {/* 左侧hello SVG艺术字动画 */}
      <svg
        width="500"
        height="180"
        viewBox="0 0 500 180"
        style={{
          position: 'absolute',
          left: 120,
          top: '38%',
          transform: 'translateY(-50%)',
          zIndex: 1,
          userSelect: 'none',
          pointerEvents: 'none',
        }}
      >
        <defs>
          <linearGradient id="hello-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#deac80" />
            <stop offset="33%" stopColor="#ffbfbb" />
            <stop offset="66%" stopColor="#ff8886" />
            <stop offset="100%" stopColor="#c35354" />
          </linearGradient>
        </defs>
        <text
          x="40"
          y="165"
          fontFamily="'Pacifico', 'Comic Sans MS', 'Brush Script MT', cursive"
          fontSize="180"
          fill="none"
          stroke="url(#hello-gradient)"
          strokeWidth="10"
          strokeDasharray="1500"
          strokeDashoffset="1500"
          className="hello-path"
        >
          hello
        </text>
      </svg>
      {/* hello下方小狗动画 */}
      <div style={{ position: 'absolute', left: 120, top: 'calc(38% + 110px)', zIndex: 1 }}>
        <div className="main">
          <div className="dog">
            <div className="dog__head">
              <div className="dog__head-c"></div>
              <div className="dog__snout"></div>
              <div className="dog__nose"></div>
              <div className="dog__eye-l"></div>
              <div className="dog__eye-r"></div>
              <div className="dog__ear-l"></div>
              <div className="dog__ear-r"></div>
            </div>
            <div className="dog__body"></div>
            <div className="dog__tail"></div>
            <div className="dog__paws">
              <div className="leg dog__bl-leg">
                <div className="paw dog__bl-paw"></div>
                <div className="top dog__bl-top"></div>
              </div>
              <div className="leg dog__fl-leg">
                <div className="paw dog__fl-paw"></div>
                <div className="top dog__fl-top"></div>
              </div>
              <div className="leg dog__fr-leg">
                <div className="paw dog__fr-paw"></div>
                <div className="top dog__fr-top"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {contextHolder}
      <Card className="auth-card" style={{ marginRight: 120, padding: '16px 16px' }}>
        <div className="auth-title" style={{ marginBottom: 8 }}>
          <BookOutlined />
          <Title level={2}>课程智能助手</Title>
          <Text type="secondary">请登录您的账号</Text>
        </div>
        
        <Form
          form={form}
          onFinish={onFinish}
          layout="vertical"
          size="large"
          style={{ gap: 8, marginBottom: 0 }}
        >
          <Form.Item 
            name="username" 
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="请输入用户名"
              disabled={loading}
            />
          </Form.Item>
          
          <Form.Item 
            name="password" 
            label="密码"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="请输入密码"
              disabled={loading}
            />
          </Form.Item>
          
          <Form.Item>
            <Button 
              className='neumorphic-btn'
              type="primary" 
              htmlType="submit"
              block 
              size="large"
              loading={loading}
              style={{
                height: 48, 
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #9370DB 0%, #8A2BE2 100%)',
                border: 'none'
              }}
            >
              {loading ? '登录中...' : '登录'}
            </Button>
          </Form.Item>
          
          <div style={{ textAlign: 'center' }}>
            <Text type="secondary">没有账号？</Text>
            <Button 
              type="link" 
              onClick={() => navigate('/register')}
              disabled={loading}
            >
              立即注册
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default Login;