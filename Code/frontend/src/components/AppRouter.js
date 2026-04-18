import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Home from '../pages/Home';
import Login from '../pages/Login';
import Register from '../pages/Register';
import Profile from '../pages/Profile';
import PrivateLayout from './PrivateLayout';
import CourseLayout from "./CourseLayout";
import CourseHomePage from "../pages/CourseHomePage";
import CourseMaterialsPage from "../pages/CourseMaterialsPage";
import CourseKnowledgePage from "../pages/CourseKnowledgePage";
import CourseQAPage from "../pages/CourseQAPage";
import CourseExercisesPage from "../pages/CourseExercisesPage";
import CourseCommunityPage from "../pages/CourseCommunityPage";
import PostDetailPage from "../pages/PostDetailPage";
import ExerciseDetailPage from "../pages/ExerciseDetailPage";

const AppRouter = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/*" element={
        <PrivateLayout>
          <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/course/:id" element={<CourseLayout />}>
                  <Route index element={<CourseHomePage />} />
                  <Route path="materials" element={<CourseMaterialsPage />} />
                  <Route path="knowledge" element={<CourseKnowledgePage />} />
                  <Route path="qa" element={<CourseQAPage />} />
                  <Route path="exercises" element={<CourseExercisesPage />} />
                  <Route path="exercises/:exerciseId" element={<ExerciseDetailPage />} />
                  <Route path="community" element={<CourseCommunityPage />} />
                  <Route path="community/:postId" element={<PostDetailPage />} />
              </Route>
          </Routes>
        </PrivateLayout>
      } />
    </Routes>
  );
};

export default AppRouter; 