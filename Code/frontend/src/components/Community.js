import React, {useEffect, useState} from 'react';
import {List, Avatar, Button, Input, Space, Modal, Radio, Pagination, Card} from 'antd';
import { EditOutlined, SearchOutlined, CommentOutlined } from '@ant-design/icons';
import {createPost, getPost} from "../service/post";
import useMessage from "antd/es/message/useMessage";
import NeumorphicPagination from "../components/NeumorphicPagination"
import AnonymousToggle from './AnonymousButton';
import '../css/neumorphism.css';
import '../css/coursecard.css';


const { TextArea } = Input;

const Community = ({ courseId, onViewPost }) => {
  const [posts, setPosts] = useState([]);
  const [postTitle, setPostTitle] = useState('');
  const [showPostModal, setShowPostModal] = useState(false);
  const [postContent, setPostContent] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [search, setSearch] = useState('');
  // 新增state
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const [messageApi, contextHolder] = useMessage();

  const loadPosts = async (keyword = '', pageNum = 1) => {
    const res = await getPost(courseId, pageNum - 1, 20, keyword);
    if (res.success) {
      setPosts(res.data.posts);
      setTotal(res.data.total);
    } else {
      // 处理错误
      console.error('获取帖子失败');
    }
    console.log(res)
  };

  useEffect(() => {
    loadPosts(search, page);
  }, [courseId, search]);

  // 发帖
  const handlePost = async () => {
    if (!postTitle.trim()) return messageApi.warning('标题不能为空');
    if (!postContent.trim()) return messageApi.warning('内容不能为空');

    try {
      const res = await createPost(courseId, {
        title: postTitle,
        content: postContent,
        is_anonymous: isAnonymous
      });

      if (res.success) {
        messageApi.success(res.message || '发帖成功');
        setPosts(prev => [res.data, ...prev]);
      } else {
        messageApi.error(res.message || '发帖失败');
      }
    } catch (e) {
      console.error("发帖异常", e);
      messageApi.error('发帖请求出错');
    }

    setPostTitle('');
    setPostContent('');
    setIsAnonymous(false);
    setShowPostModal(false);
  };

  return (
    <div>
      {contextHolder}
      {/* 顶部操作区 */}
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 24, gap: 16 }}>
        <Input
           className="neumorphic-input simple-search"
          prefix={<SearchOutlined />}
          placeholder="搜索帖子/作者/关键词..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          allowClear
    style={{ flex: 1, minWidth: 0 }} 
        />
        <Button
      className="neumorphic-btn"
      type="primary"
      size="middle"
      onClick={() => setShowPostModal(true)}
      style={{ marginLeft: 12, whiteSpace: 'nowrap' }} 
    >
    发帖
        </Button>
      </div>
      {/* 帖子列表 */}
      <List
        dataSource={posts}
        locale={{emptyText: '暂无帖子'}}
        renderItem={(item, idx) => (
          <List.Item 
            style={{ padding: 0, border: 'none', background: 'transparent' }}>
            <Card
              size="small"
              className="course-card material-card"
              style={{
                width: '100%',
                marginBottom: 20,
                background: idx % 2 === 0 ? 'rgba(200, 227, 246, 0.6)' : 'rgba(154, 197, 230, 0.6)',
                padding: 0,
                position: 'relative',
                border: 0
              }}
            >
              {/* 标题区 */}
              <div style={{ padding: '20px 32px 0 32px', fontSize: 19, fontWeight: 700, color: '#334155', cursor: 'pointer' }} onClick={() => onViewPost && onViewPost(item)}>
                {item.title}
              </div>
              {/* 内容摘要 */}
              <div style={{ padding: '10px 32px 0 32px', fontSize: 16, color: '#222', cursor: 'pointer', minHeight: 32 }} onClick={() => onViewPost && onViewPost(item)}>
                {item.content.length > 60 ? item.content.slice(0, 60) + '...' : item.content}
              </div>
              {/* 作者/时间/评论数 */}
              <div style={{ display: 'flex', alignItems: 'center', padding: '16px 32px 12px 32px', color: '#64748b', fontSize: 14 }}>
                <Avatar
                    style={{ backgroundColor: item.is_anonymous ? '#aaa' : '#fff', marginRight: 8 }}
                    size={28}
                >
                  {item.is_anonymous
                    ? '匿'
                    : item.author_role === 'teacher'
                      ? '🧑‍🏫'
                      : item.author_role === 'student'
                        ? '🧑‍🎓'
                        : (item.author?.charAt(0).toUpperCase() || '?')}
                </Avatar>
                <span style={{ fontWeight: 500 }}>{item.author}</span>
                <span style={{ margin: '0 16px', color: '#b4b4b4' }}>|</span>
                <span>{new Date(item.created_at).toLocaleString()}</span>
                <span style={{ flex: 1 }} />
                <Button
                  className="coursecard-btn coursecard-btn-dissolve"
                  size="middle"
                  onClick={() => onViewPost && onViewPost(item)}
                  style={{ minWidth: 60, background: idx % 2 === 0 ? 'rgba(200, 227, 246, 0.6)' : 'rgba(154, 197, 230, 0.6)' }}
                >
                  查看详情 / 评论
                </Button>
              </div>
            </Card>
          </List.Item>
        )}
      />

      {/* 新增分页控件 */}
      
      <NeumorphicPagination 
  current={page} 
  total={total} 
  pageSize={20} 
  onChange={p => setPage(p)} 
/>

      {/* 发帖弹窗 */}
      <Modal
  className="neumorphic-modal"
  title="发新帖"
  open={showPostModal}
  onCancel={() => setShowPostModal(false)}
  footer={null}  // 关闭默认底部按钮
>
  <Input
    value={postTitle}
    onChange={e => setPostTitle(e.target.value)}
    placeholder="输入标题（必填）"
    style={{ marginBottom: 12 }}
  />
  <TextArea
    value={postContent}
    onChange={e => setPostContent(e.target.value)}
    rows={4}
    placeholder="分享你的观点、提问或经验..."
    style={{ marginBottom: 12 }}
  />

  <Space style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
    <AnonymousToggle isAnonymous={isAnonymous} onToggle={setIsAnonymous} />
    <Button
      type="primary"
      onClick={handlePost}
    >
      发布
    </Button>
  </Space>
</Modal>
    </div>
  );
};

export default Community; 