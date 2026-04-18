import React from 'react';
import CourseHome from '../components/CourseHome';
import { useParams } from 'react-router-dom';

const CourseHomePage = () => {
    const { id } = useParams();
    return <CourseHome courseId={id} />;
};

export default CourseHomePage;
