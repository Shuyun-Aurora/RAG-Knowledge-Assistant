import React from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { HomeOutlined, UserOutlined } from '@ant-design/icons';
import '../css/header.css';

const AppHeader = ({ title, isCoursePage = false }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams();

  const getActiveNav = () => {
    if (!isCoursePage) return '';
    const path = location.pathname;
    if (path.includes('materials')) return 'materials';
    if (path.includes('exercises')) return 'exercises';
    if (path.includes('community')) return 'community';
    return 'home';
  };

  const activeNav = getActiveNav();

  return (
    <header className="header-container">
      <div className="header-content">
        <div className="header-left">
          <h1 className="course-title">{title}</h1>
        </div>

        {isCoursePage ? (
          <nav className="course-nav header-center">
            <button
              className={`course-nav-item ${activeNav === 'home' ? 'active' : ''}`}
              onClick={() => navigate(`/course/${id}`)}
            >
              课程主页
            </button>
            <button
              className={`course-nav-item ${activeNav === 'materials' ? 'active' : ''}`}
              onClick={() => navigate(`/course/${id}/materials`)}
            >
              课程资料
            </button>
            <button
              className={`course-nav-item ${activeNav === 'exercises' ? 'active' : ''}`}
              onClick={() => navigate(`/course/${id}/exercises`)}
            >
              课程习题
            </button>
            <button
              className={`course-nav-item ${activeNav === 'community' ? 'active' : ''}`}
              onClick={() => navigate(`/course/${id}/community`)}
            >
              课程社区
            </button>
          </nav>
        ) : (
          <div className="header-center"></div>
        )}

        <div className="user-actions header-right">
          <button
            className='header-btn-custom'
            onClick={() => navigate('/')}
          >
            <HomeOutlined style={{ marginRight: 8 }} /> 首页
          </button>
          <button
            className='header-btn-custom'
            onClick={() => navigate('/profile')}
          >
            <UserOutlined style={{ marginRight: 8 }} /> 个人中心
          </button>
        </div>
      </div>
    </header>
  );
};

export default AppHeader;
