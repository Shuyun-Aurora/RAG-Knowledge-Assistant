import React, {useState, useEffect, useContext, useRef} from 'react';
import {Row, Col, Typography, Input, Button, Layout, Tabs, Modal, Pagination} from 'antd';
import { bannerData } from '../data/mockData';
import AppHeader from '../components/Header';
import CourseCard from '../components/CourseCard';
import BannerCarousel from '../components/BannerCarousel';
import CourseCreateModal from '../components/CourseCreateModal';
import 'antd/dist/reset.css';
import useMessage from "antd/es/message/useMessage";
import {getAllCourses, getJoinedCourses, getTaughtCourses, joinCourse, quitCourse, dissolveCourse} from '../service/course';
import UserContext from "../contexts/UserContext";
import '../css/global.css';
import NeumorphicPagination from "../components/NeumorphicPagination"
import { EditOutlined, SearchOutlined, CommentOutlined } from '@ant-design/icons';
import StyledTabs from '../components/StyledTabs.tsx';

const { Content } = Layout;
const { Title } = Typography;
const { Search } = Input;

const PAGE_SIZE = 12;  // 每页显示12条

const Home = () => {
  const [searchText, setSearchText] = useState('');
  const [tab, setTab] = useState('my');
  const [joinedCourses, setJoinedCourses] = useState([]); // 只存id
  const [courseList, setCourseList] = useState([]);
  const [totalCourses, setTotalCourses] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [openModal, setOpenModal] = useState(false); //新增开课弹窗
  const [previewCourse, setPreviewCourse] = useState(null);   //预览弹窗
  const user = useContext(UserContext);
  const searchInputRef = useRef(null);

  // 判断身份
  const isStudent = user?.role === 'student';
  const isTeacher = user?.role === 'teacher';

  // Tabs
  const showTabs = isStudent || isTeacher;
  const tabItems = [
    { key: 'my', label: isStudent ? '我的课程' : '我开设的课程' },
    { key: 'all', label: '全部课程' }
  ];
  const [messageApi, contextHolder] = useMessage();

  // 根据tab、搜索和分页拉数据
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
      } 
    } catch (e) {
      messageApi.error('获取课程请求失败');
    }
  };

  useEffect(() => {
    setCurrentPage(1);  // tab 或搜索关键词变更时，重置到第一页
  }, [tab, searchText]);

  useEffect(() => {
    fetchCourses(currentPage, searchText);
  }, [tab, currentPage, searchText]);

  useEffect(() => {
    if (isStudent) {
      getJoinedCourses().then(res => {
        if (res.success) {
          setJoinedCourses(res.data.courses.map(c => c.id));
        }
      });
    }
  }, [isStudent]);

  // 加入课程
  const handleJoin = async (courseId) => {
    if (joinedCourses.includes(courseId)) return;

    try {
      const res = await joinCourse(courseId);
      if (res.success) {
        setJoinedCourses(prev => [...prev, courseId]);
        setCourseList(prev =>
            prev.map(c =>
                c.id === courseId
                    ? { ...c, student_count: c.student_count + 1 }
                    : c
            )
        );
        messageApi.success(res.message || '加入课程成功！');
      } else {
        messageApi.error(res.message || '加入课程失败');
      }
    } catch (e) {
      messageApi.error('加入课程请求失败');
    }
  };

  // 退出课程
  const handleQuit = async (courseId) => {
    if (!joinedCourses.includes(courseId)) return;
    try {
      const res = await quitCourse(courseId);
      if (res.success) {
        setJoinedCourses(prev => prev.filter(id => id !== courseId));
        setCourseList(prev =>
            prev.map(c =>
                c.id === courseId
                    ? { ...c, student_count: Math.max(0, c.student_count - 1) }
                    : c
            )
        );
        messageApi.success(res.message || '退出课程成功');
      } else {
        messageApi.error(res.message || '退出课程失败');
      }
    } catch (e) {
      messageApi.error('退出课程请求失败');
    }
  };

  // 解散课程
  const handleDissolve = async (courseId) => {
    try {
      const res = await dissolveCourse(courseId);
      if (res.success) {
        messageApi.success(res.message || '课程已成功解散');
        // 更新课程列表
        fetchCourses(currentPage, searchText);
      } else {
        messageApi.error(res.message || '解散课程失败');
      }
    } catch (e) {
      messageApi.error('解散课程请求失败');
    }
  };

  // 新增开课成功回调
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
              <StyledTabs
  activeKey={tab}
  onChange={setTab}
  centered
  size="large"
  items={tabItems}
/>
            </div>
          )}
  
  <div className="search-container">
  <Input
    className="neumorphic-input simple-search"
    prefix={<SearchOutlined style={{ color: '#888' }} />}
    placeholder="搜索课程名称或教师姓名..."
    value={searchText}
    onChange={e => setSearchText(e.target.value)}
    onPressEnter={() => setCurrentPage(1)}
    allowClear
    style={{ flex: 1, minWidth: 0 }}  // 重点，填满剩余空间
  />
  {isTeacher && (
    <Button
      className="neumorphic-btn"
      type="primary"
      size="middle"
      onClick={() => setOpenModal(true)}
      style={{ marginLeft: 12, whiteSpace: 'nowrap' }}  // 保证按钮不缩小
    >
      新增开课
    </Button>
  )}
</div>

          {/* 课程列表透明容器 */}
          <div className="courses-container">
            {courseList.length === 0 ? (
              <div className="neumorphic-container" style={{ textAlign: 'center', padding: '48px 0', fontSize: 18 }}>
                {/* 空状态提示 */}
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
              <p><b>授课教师：</b>{previewCourse.teacher?.username || '未知'}</p>
              <p><b>简介：</b>{previewCourse.description}</p>
              <p style={{ marginTop: 16 }}>加入课程后可进入详情页查看更多内容</p>
            </Modal>
          )}
        </div>
      </Content>
    </Layout>
  );
};

export default Home;