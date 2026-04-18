import React, { useContext, useState, useEffect } from 'react';
import ExerciseList from '../components/ExerciseList';
import UploadExercise from '../components/UploadExercise';
import UserContext from '../contexts/UserContext';
import CourseContext from "../contexts/CourseContext";
import {deleteExerciseSet, fetchExercises} from "../service/exercise";

const CourseExercisesPage = () => {
    const user = useContext(UserContext);
    const isTeacher = user.role === 'teacher';
    const { courseId } = useContext(CourseContext);

    const [exercises, setExercises] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const pageSize = 5;

    const loadExercises = async (pageToLoad = 1) => {
        try {
            const res = await fetchExercises(courseId, pageToLoad, pageSize, '');
            if (res.success) {
                setExercises(res.data.items);
                setTotal(res.data.total);
                setPage(pageToLoad);
            } else {
                setExercises([]);
                setTotal(0);
            }
        } catch (e) {
            console.error('Failed to fetch exercises:', e);
            setExercises([]);
            setTotal(0);
        }
    };

    // 拉取习题数据
    useEffect(() => {
        if (courseId) {
            loadExercises();
        }
    }, [courseId]);


    const reloadExercises = async () => {
        try {
            const res = await fetchExercises(courseId, 1, 10, '');
            if (res.success) setExercises(res.data.items);
            else setExercises([]);
        } catch {
            setExercises([]);
        }
    };

    // 删除习题集
    const handleDelete = async (item) => {
        const res = await deleteExerciseSet(item.id);
        if (!res.success) {
            throw new Error(res.message || '删除失败');
        }
        // 删除后重新加载当前页（防止页码变化可选设置为 page）
        await loadExercises(page);
    };

    return (
        <>
            {isTeacher && (
                <UploadExercise
                    onNewExercise={reloadExercises}
                />
            )}
            <ExerciseList
                exercises={exercises}
                total={total}
                pageSize={pageSize}
                isTeacher={isTeacher}
                onPageChange={(newPage) => loadExercises(newPage)}
                current={page}
                onDelete={handleDelete}
            />
        </>
    );
};

export default CourseExercisesPage;
