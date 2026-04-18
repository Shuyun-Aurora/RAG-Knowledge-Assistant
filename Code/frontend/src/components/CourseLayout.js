import React, { useContext, useEffect, useState } from 'react';
import { Outlet, useParams } from 'react-router-dom';
import CourseContext from '../contexts/CourseContext';
import AppHeader from '../components/Header';
import { getCourseById } from "../service/course";
import '../css/global.css';

const CourseLayout = () => {
  const { id } = useParams();
  const [course, setCourse] = useState(null);

  useEffect(() => {
    const fetchCourse = async () => {
      const res = await getCourseById(id);
      setCourse(res.data);
    };
    fetchCourse();
  }, [id]);

  return (
    <CourseContext.Provider value={{ courseId: id, course }}>
      <div style={{ minHeight: '100vh' }}>
        <AppHeader title={course?.name || "课程详情"} isCoursePage />
        
        <main style={{ 
          maxWidth: 1600, 
          margin: '0 auto', 
          padding: '2rem',
        }}>
          <Outlet />
        </main>
      </div>
    </CourseContext.Provider>
  );
};

export default CourseLayout;