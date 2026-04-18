import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PostDetail from '../components/PostDetail';
import { getPostById } from '../service/post'; // 你之前写的api文件里，getPostById接口

const PostDetailPage = () => {
    const { id, postId } = useParams();
    const navigate = useNavigate();

    const [post, setPost] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function fetchPost() {
            try {
                const res = await getPostById(postId);
                if (res.success) {
                    setPost(res.data);
                } else {
                    setError('帖子不存在');
                }
            } catch (e) {
                setError('请求失败');
            }
        }
        fetchPost();
    }, [id, postId]);

    if (error) return <div>{error}</div>;
    if (!post) return <div>帖子不存在</div>;

    console.log('id:', id);
    console.log('post_id:', postId);
    console.log('post:', post);

    return (
        <PostDetail post={post} onBack={() => navigate(-1)} />
    );
};

export default PostDetailPage;
