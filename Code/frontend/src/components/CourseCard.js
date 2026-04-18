import React, { useState } from 'react';
import { Card, Typography, Button, Modal, Tag } from 'antd';
import { BookOutlined, UserOutlined, InfoCircleOutlined, TeamOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import '../css/coursecard.css';

const { Title, Text } = Typography;

const CourseCard = ({ course, isJoined, onJoin, onQuit, isStudent, onPreview, canEnterDetail, onDissolve, user, index }) => {
  const navigate = useNavigate();
  const isTeacher = !isStudent;
  const isDissolved = course.is_deleted;
  const [isModalVisible, setIsModalVisible] = useState(false);

  // 交替背景色
  const bgColor = index % 2 === 0 ? 'rgba(200, 227, 246, 0.6)' : 'rgba(154, 197, 230, 0.6)';

  const handleJoin = (e) => {
    e.stopPropagation();
    if (onJoin) onJoin(course.id);
  };
  
  const handleQuit = (e) => {
    e.stopPropagation();
    if (onQuit) onQuit(course.id);
  };

  const handleDissolve = (e) => {
    e.stopPropagation();
    setIsModalVisible(true);
  };

  const handleOk = () => {
    if (onDissolve) onDissolve(course.id);
    setIsModalVisible(false);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
  };
  
  const handleCardClick = () => {
    if (canEnterDetail) {
      navigate(`/course/${course.id}`);
    } else if (onPreview) {
      onPreview();
    }
  };

  return (
    <>
      <div className="card-wrap">
        <div
          className="course-card"
          onClick={handleCardClick}
          style={{
            background: bgColor,
            width: 260,
            minWidth: 220,
            maxWidth: 280,
            margin: '0 auto',
            height: 240, // 固定卡片高度
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          {/* 信息蒙版层 */}
          <div
            className="course-card-overlay"
            style={{
              fontFamily: "'Inter', sans-serif",
              lineHeight: 1.5,
              position: 'relative',
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'flex-start',
            }}
          >
            {/* 左上角图标 */}
            <BookOutlined
              style={{
                position: 'absolute',
                left: 0,
                top: 0,
                fontSize: 32,
                color: '#7bb1d1',
                opacity: 0.7,
                margin: 8,
              }}
            />
  
            {/* 信息区 */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '16px', // 缩小按钮与文字的间距
                marginTop: '0px', // 标题距离顶部更近
              }}
            >
    <Title
      level={2}
      style={{
        margin: 0,
        fontWeight: '900',
        fontSize: '20px',
        textAlign: 'center',
        userSelect: 'none',
      }}
    >
      {course.name}
    </Title>
  </div>
  
            <Text className="course-info-text">
              <UserOutlined
                style={{ marginRight: 6, color: '#7bb1d1', fontSize: 17 }}
              />
    授课教师：{course.teacher.username}
  </Text>
  
            <Text className="course-info-text">
              <TeamOutlined
                style={{ marginRight: 6, color: '#7bb1d1', fontSize: 16 }}
              />
    已选学生：{course.student_count} 人
  </Text>

</div>

          {/* 操作按钮区（始终占位，保证高度一致） */}
          <div className="card-btn-group" style={{ minHeight: 48, display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: '-20px' }} onClick={(e) => e.stopPropagation()}>
            {isDissolved ? (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: 'rgba(0,0,0,0.12)',
                  color: '#666',
                  fontWeight: 600,
                  fontSize: '16px',
                  borderRadius: '14px',
                  height: 40,
                  minWidth: 100,
                  padding: '0 18px',
                  userSelect: 'none',
                  border: 'none',
                  boxShadow: 'none',
                }}
              >
                已解散
              </span>
            ) : (
              <>
                {isStudent && !isJoined && (
              <Button 
                  className="coursecard-btn coursecard-btn-dissolve"
                  size="middle"
                  onClick={handleJoin}
                  style={{
                    background:
                      index % 2 === 0
                        ? 'rgba(200, 227, 246, 0.6)'
                        : 'rgba(154, 197, 230, 0.6)',
                  }}
              >

                加入课程
              </Button>
            )}
                {isStudent && isJoined && (
              <Button 
                    className="coursecard-btn coursecard-btn-danger"
                    size="middle"
                onClick={handleQuit}
                style={{ minWidth: 60, background: index % 2 === 0 ? 'rgba(200, 227, 246, 0.6)' : 'rgba(154, 197, 230, 0.6)' }}
              >
                退出课程
              </Button>
            )}
                {isTeacher && course.teacher.id === user?.id && (
              <Button 
                    className="coursecard-btn coursecard-btn-danger"
                    size="middle"
                onClick={handleDissolve}
                style={{
                  background:
                    index % 2 === 0
                      ? 'rgba(200, 227, 246, 0.6)'
                      : 'rgba(154, 197, 230, 0.6)',
                }}
              >
                解散课程
              </Button>
                )}
              </>
            )}
      </div>

          {/* 解散确认弹窗 */}
      <Modal
        className="neumorphic-modal"
        title="确认解散课程"
        open={isModalVisible}
        onOk={handleOk}
        onCancel={handleCancel}
        okText="确定"
        cancelText="取消"
        okType="danger"
      >
        <p>确定要解散这个课程吗？</p>
        <p>解散后，学生将无法进行任何操作，但可以查看历史记录。此操作不可逆。</p>
      </Modal>
        </div>
      </div>
    </>
  );
}
export default CourseCard;