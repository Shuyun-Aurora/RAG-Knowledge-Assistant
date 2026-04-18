import React, {useEffect, useRef, useState} from 'react';
import {Typography, Avatar, Space, List, Input, Button, Divider,Card, Checkbox} from 'antd';
import { CommentOutlined, LeftOutlined } from '@ant-design/icons';
import InfiniteScroll from "react-infinite-scroll-component";
import { getComments, addComment } from '../service/post';
import AnonymousToggle from './AnonymousButton';
import '../css/post.css';

const { Text } = Typography;
const PAGE_SIZE = 10;

const PostDetail = ({ post, onBack }) => {
  const [comments, setComments] = useState([]);
  const [commentContent, setCommentContent] = useState('');
  const [replyTo, setReplyTo] = useState(null); // 当前回复的评论 ID
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const commentRefs = useRef({}); // 存放评论 DOM 引用用于跳转
  const [isAnonymous, setIsAnonymous] = useState(false);

  const postId = post.id;

  // 加载第一页评论
  useEffect(() => {
    const fetchInitialComments = async () => {
      const res = await getComments(postId, 0, PAGE_SIZE);
      if (res.success) {
        setComments(res.data.comments);
        setSkip(res.data.comments.length);
        if (res.data.comments.length < PAGE_SIZE) setHasMore(false);
      }
    };
    fetchInitialComments();
  }, [postId]);

  const loadMoreComments = async () => {
    const res = await getComments(postId, skip, PAGE_SIZE); // 分页获取评论
    if (res.success) {
      const newComments = res.data.comments;
      if (newComments.length === 0) {
        setHasMore(false); // 后端没了，明确告诉前端停止
        return;
      }
      setComments(prev => [...prev, ...newComments]);
      setSkip(prev => prev + newComments.length);
      if (newComments.length < PAGE_SIZE) setHasMore(false);
    }
  };

  const handleComment = async (content) => {
    if (!content.trim()) return;
    const res = await addComment(postId, content, replyTo?.id || null, isAnonymous); // 传 parentId
    if (res.success) {
      const newComment = res.data;
      setComments(prev => [...prev, newComment]);
      setSkip(prev => prev + 1); // 增加 skip
      setCommentContent('');

      // 提交成功后滚动到底部
      setTimeout(() => {
        const box = document.getElementById("scrollable-comment-box");
        if (box) {
          box.scrollTo({ top: box.scrollHeight, behavior: "smooth" });
        }
      }, 100);
    }
  };

  const handleReply = (comment) => {
    setReplyTo(comment);
    const input = document.getElementById("comment-input");
    input?.focus();
  };

  const scrollToComment = (id) => {
    const target = commentRefs.current[id];
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "center" });

      // 添加高亮 class
      target.classList.add("highlighted-comment");

      // 一段时间后移除高亮
      setTimeout(() => {
        target.classList.remove("highlighted-comment");
      }, 1500);
    }
  };

  if (!post) return <div>未找到该帖子</div>;

  return (
    <Card 
      className='neumorphic-card'
      style={{ 
      width: '100%', 
      background: 'transparent', 
      borderRadius: 16, 
      boxShadow: '0 2px 12px #e0e7ef22', 
      padding: 0
    }}>
      {/* 顶部信息区 */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        padding: '28px 32px 0 32px', 
        borderRadius: '16px 16px 0 0', 
        borderBottom: '1px solid #f0f0f0', 
        background: 'transparent'
      }}>
        <Button type="link" icon={<LeftOutlined />} onClick={onBack} style={{ color: '#64748b', fontWeight: 500, padding: 0, marginRight: 16 }}>
          返回社区
        </Button>
        <span style={{ fontSize: 22, fontWeight: 700, color: '#334155', flex: 1 }}>{post.title}</span>
        <Space size={16}>
          <Avatar style={{ backgroundColor: post.is_anonymous ? '#aaa' : '#fff' }} size={36} >
              {post.isAnonymous
                ? '匿'
                : post.author_role === 'teacher'
                  ? '🧑‍🏫'
                  : post.author_role === 'student'
                    ? '🧑‍🎓'
                    : (post.author?.[0] || '?')}
          </Avatar>
          <Text style={{ fontWeight: 500 }}>{post.author}</Text>
          <Text type="secondary" style={{ fontSize: 13 }}>{post.time}</Text>
          <Text type="secondary" style={{ fontSize: 15 }}><CommentOutlined /> {comments.length}</Text>
        </Space>
      </div>
      
      {/* 帖子内容 */}
      <div style={{ 
        padding: '32px 32px 0 32px', 
        fontSize: 17, 
        color: '#222', 
        lineHeight: 1.8, 
        minHeight: 80
      }}>
        {post.content}
      </div>
      
      <Divider style={{ margin: '24px 0 0 0' }} />

      {/* 评论区 */}
      <div style={{ padding: '0 32px 32px 32px' }}>
        <div style={{ fontWeight: 500, marginTop: 12, marginBottom: 12, color: '#334155', fontSize: 17 }}>
          <CommentOutlined /> 全部评论
        </div>

        {/* 评论滚动区 */}
        <div id="scrollable-comment-box" style={{ maxHeight: 300, overflow: 'auto', marginBottom: 16 }}>
          <InfiniteScroll
              dataLength={comments.length}
              next={loadMoreComments}
              hasMore={hasMore}
              loader={<div style={{ textAlign: 'center', padding: 8, color: '#999' }}>
                {hasMore ? "加载中..." : "没有更多评论了"}
              </div>}
              scrollableTarget="scrollable-comment-box"
          >
            <List
                dataSource={comments}
                locale={{ emptyText: '暂无评论' }}
                renderItem={c => (
                    <List.Item
                        key={c.id}
                        style={{ padding: '12px 0' }}
                        ref={el => {
                          if (el) commentRefs.current[c.id] = el;
                        }}
                    >
                      <div style={{ width: '100%' }}>
                        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                          {/* 左侧：头像 + 用户 + 内容 */}
                          <Avatar
                              size={28}
                              style={{ backgroundColor: c.is_anonymous ? '#aaa' : '#fff'}}
                          >
                            {c.is_anonymous
                              ? '匿'
                              : c.user_role === 'teacher'
                                ? '🧑‍🏫'
                                : c.user_role === 'student'
                                  ? '🧑‍🎓'
                                  : (c.user?.[0] || '?')}
                          </Avatar>
                          <Text style={{ fontSize: 15 }}>{c.user}：</Text>
                          <Text style={{ fontSize: 15 }}>{c.content}</Text>

                          {/* 右侧：操作按钮 + 时间 */}
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginLeft: 'auto' }}>

                            {c.parent_id && (
                                <Button
                                    type="text"
                                    size="small"
                                    style={{ color: '#999' }}
                                    onClick={() => scrollToComment(c.parent_id)}
                                >
                                  ↩ 查看回复内容
                                </Button>
                            )}
                            <Button size="small" type="link" onClick={() => handleReply(c)}>回复</Button>

                            <Text type="secondary" style={{ fontSize: 12 }}>{c.time}</Text>
                          </div>
                        </div>
                      </div>
                    </List.Item>

                )}
            />
          </InfiniteScroll>
        </div>

        {replyTo && (
            <div style={{ marginBottom: 4, color: '#999' }}>
              正在回复 <b>@{replyTo.user}</b>
              <Button size="small" type="link" onClick={() => setReplyTo(null)}>取消</Button>
            </div>
        )}

        {/* 评论输入框 */}
        <div style={{ display: 'flex', gap: 8 }}>
        <AnonymousToggle isAnonymous={isAnonymous} onToggle={setIsAnonymous} />
          <Input
              className='neumorphic-input'
              id="comment-input"
              value={commentContent}
              onChange={e => setCommentContent(e.target.value)}
              placeholder="写下你的评论..."
              size="large"
              style={{ flex: 1 }}
          />
          <Button
              className='neumorphic-btn'
              type="primary"
              onClick={() => handleComment(commentContent)}
              disabled={!commentContent.trim()}>评论
          </Button>
        </div>
        </div>
    </Card>
  );
};

export default PostDetail; 