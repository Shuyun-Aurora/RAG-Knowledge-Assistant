import React from 'react';
import { Card } from 'antd';
import Community from '../components/Community';
import {useNavigate, useParams} from 'react-router-dom';

const CourseCommunityPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();

    // 这里不维护帖子列表，交给 Community 自己管理
    return (
        <Card  className="neumorphic-card" title="课程社区">
            <Community
                courseId={id}
                onViewPost={(post) => navigate(`/course/${id}/community/${post.id}`)}
            />
        </Card>
    );
};


export default CourseCommunityPage;
