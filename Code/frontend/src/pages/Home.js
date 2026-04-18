import React, { useContext, useEffect, useRef, useState } from 'react';
import { Button, Col, Input, Layout, Modal, Row, Typography } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import useMessage from 'antd/es/message/useMessage';
import 'antd/dist/reset.css';

import BannerCarousel from '../components/BannerCarousel';
import CourseCard from '../components/CourseCard';
import CourseCreateModal from '../components/CourseCreateModal';
import AppHeader from '../components/Header';
import NeumorphicPagination from '../components/NeumorphicPagination';
import StyledTabs from '../components/StyledTabs.tsx';
import UserContext from '../contexts/UserContext';
import {
  dissolveCourse,
  getAllCourses,
  getJoinedCourses,
  getTaughtCourses,
  joinCourse,
  quitCourse,
} from '../service/course';
import '../css/global.css';

const { Content } = Layout;

const PAGE_SIZE = 12;
const bannerData = [
  {
    img: 'https://img.remit.ee/api/file/BQACAgUAAyEGAASHRsPbAAImVWhc8Su4goN4MuMgnBVE38EwyYa-AAKkFgACvxDoVrSO_4TzL6PNNgQ.jpg',
    title: '欢迎来到课程智能助手',
    desc: '智能学习，轻松掌握每一门课程',
  },
  {
    img: 'https://img.remit.ee/api/file/BQACAgUAAyEGAASHRsPbAAIr42hl6BF0JVXjOL-LHYMGmQ6Q5ENuAAKrGAACPnsxV1FPhaeIkU1_NgQ.jpg',
    title: '优质课程推荐',
    desc: '发现更多优质课程，提升自我',
  },
  {
    img: 'https://img.remit.ee/api/file/BQACAgUAAyEGAASHRsPbAAIr5Ghl6BK3LFz4QREYh9WqwauCbnptAAKsGAACPnsxV25CLs0-gab8NgQ.jpg',
    title: '课程学习与交流',
    desc: '在资料、习题和社区中持续推进学习',
  }
];

const Home = () => {
  const [searchText, setSearchText] = useState('');
  const [tab, setTab] = useState('my');
  const [joinedCourses, setJoinedCourses] = useState([]);
  const [courseList, setCourseList] = useState([]);
  const [totalCourses, setTotalCourses] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [openModal, setOpenModal] = useState(false);
  const [previewCourse, setPreviewCourse] = useState(null);
  const user = useContext(UserContext);
  const searchInputRef = useRef(null);
  const [messageApi, contextHolder] = useMessage();

  const isStudent = user?.role === 'student';
  const isTeacher = user?.role === 'teacher';
  const showTabs = isStudent || isTeacher;
  const tabItems = [
    { key: 'my', label: isStudent ? '我的课程' : '我开设的课程' },
    { key: 'all', label: '全部课程' },
  ];

  const refreshJoinedCourses = async () => {
    if (!isStudent) {
      setJoinedCourses([]);
      return;
    }

    try {
      const res = await getJoinedCourses({ page: 1, pageSize: 1000, keyword: '' });
      if (res.success) {
        setJoinedCourses(res.data.courses.map((course) => course.id));
      } else {
        setJoinedCourses([]);
      }
    } catch (error) {
      setJoinedCourses([]);
    }
  };

  const fetchCourses = async (page, keyword) => {
    try {
      let res;
      if (tab === 'my') {
        if (isStudent) {
          res = await getJoinedCourses({ page, pageSize: PAGE_SIZE, keyword });
        } else if (isTeacher) {
          res = await getTaughtCourses({ page, pageSize: PAGE_SIZE, keyword });
        } else {
          res = { success: true, data: { courses: [], total: 0 } };
        }
      } else {
        res = await getAllCourses({ page, pageSize: PAGE_SIZE, keyword });
      }

      if (res.success) {
        setCourseList(res.data.courses);
        setTotalCourses(res.data.total);
      } else {
        setCourseList([]);
        setTotalCourses(0);
      }
    } catch (error) {
      setCourseList([]);
      setTotalCourses(0);
      messageApi.error('获取课程失败');
    }
  };

  useEffect(() => {
    setCurrentPage(1);
  }, [tab, searchText]);

  useEffect(() => {
    fetchCourses(currentPage, searchText);
  }, [tab, currentPage, searchText]);

  useEffect(() => {
    refreshJoinedCourses();
  }, [isStudent]);

  const handleJoin = async (courseId) => {
    if (joinedCourses.includes(courseId)) return;

    try {
      const res = await joinCourse(courseId);
      if (res.success) {
        await refreshJoinedCourses();
        await fetchCourses(currentPage, searchText);
        messageApi.success(res.message || '加入课程成功');
      } else {
        messageApi.error(res.message || '加入课程失败');
      }
    } catch (error) {
      messageApi.error('加入课程失败');
    }
  };

  const handleQuit = async (courseId) => {
    if (!joinedCourses.includes(courseId)) return;

    try {
      const res = await quitCourse(courseId);
      if (res.success) {
        await refreshJoinedCourses();
        if (tab === 'my' && courseList.length === 1 && currentPage > 1) {
          setCurrentPage((prev) => prev - 1);
        } else {
          await fetchCourses(currentPage, searchText);
        }
        messageApi.success(res.message || '退出课程成功');
      } else {
        messageApi.error(res.message || '退出课程失败');
      }
    } catch (error) {
      messageApi.error('退出课程失败');
    }
  };

  const handleDissolve = async (courseId) => {
    try {
      const res = await dissolveCourse(courseId);
      if (res.success) {
        messageApi.success(res.message || '课程已解散');
        fetchCourses(currentPage, searchText);
      } else {
        messageApi.error(res.message || '解散课程失败');
      }
    } catch (error) {
      messageApi.error('解散课程失败');
    }
  };

  const handleCreateCourseSuccess = () => {
    setOpenModal(false);
    fetchCourses(currentPage, searchText);
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#e0e5ec' }}>
      {contextHolder}
      <AppHeader title="课程智能助手" />

      <Content style={{ padding: '24px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <BannerCarousel banners={bannerData} />

          {showTabs && (
            <div style={{ display: 'flex', justifyContent: 'center', margin: '40px 0 0 0' }}>
              <StyledTabs activeKey={tab} onChange={setTab} centered size="large" items={tabItems} />
            </div>
          )}

          <div className="search-container">
            <Input
              ref={searchInputRef}
              className="neumorphic-input simple-search"
              prefix={<SearchOutlined style={{ color: '#888' }} />}
              placeholder="搜索课程名称或教师姓名..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onPressEnter={() => setCurrentPage(1)}
              allowClear
              style={{ flex: 1, minWidth: 0 }}
            />
            {isTeacher && (
              <Button
                className="neumorphic-btn"
                type="primary"
                size="middle"
                onClick={() => setOpenModal(true)}
                style={{ marginLeft: 12, whiteSpace: 'nowrap' }}
              >
                新增开课
              </Button>
            )}
          </div>

          <div className="courses-container">
            {courseList.length === 0 ? (
              <div className="neumorphic-container" style={{ textAlign: 'center', padding: '48px 0', fontSize: 18 }}>
                暂无课程
              </div>
            ) : (
              <Row gutter={[16, 16]}>
                {courseList.map((course, idx) => (
                  <Col xs={24} sm={12} md={8} lg={6} key={course.id}>
                    <CourseCard
                      course={course}
                      isStudent={isStudent}
                      isJoined={joinedCourses.includes(course.id)}
                      onJoin={handleJoin}
                      onQuit={handleQuit}
                      onPreview={() => setPreviewCourse(course)}
                      onDissolve={handleDissolve}
                      canEnterDetail={
                        isStudent
                          ? joinedCourses.includes(course.id)
                          : isTeacher && course.teacher.id === user?.id
                      }
                      user={user}
                      index={idx}
                    />
                  </Col>
                ))}
              </Row>
            )}

            <NeumorphicPagination
              current={currentPage}
              total={totalCourses}
              pageSize={PAGE_SIZE}
              onChange={setCurrentPage}
            />
          </div>

          <CourseCreateModal
            open={openModal}
            onCancel={() => setOpenModal(false)}
            onSuccess={handleCreateCourseSuccess}
          />

          {previewCourse && (
            <Modal
              classname="neumorphic-modal"
              open={!!previewCourse}
              title={previewCourse.name}
              onCancel={() => setPreviewCourse(null)}
              footer={null}
            >
              <p>
                <b>授课教师：</b>
                {previewCourse.teacher?.username || '未知'}
              </p>
              <p>
                <b>简介：</b>
                {previewCourse.description}
              </p>
              <p style={{ marginTop: 16 }}>加入课程后可进入详情页查看更多内容。</p>
            </Modal>
          )}
        </div>
      </Content>
    </Layout>
  );
};

export default Home;
