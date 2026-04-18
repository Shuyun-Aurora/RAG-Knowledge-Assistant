import React, { useContext, useEffect, useState } from 'react';
import { Card, Button } from 'antd';
import KnowledgeGraph from '../components/KnowledgeGraph';
import KnowledgeGraph2 from '../components/KnowledgeGraph2';
import ResizableBox from 'react-resizable-box';
import { getKnowledgeGraph } from '../service/knowledge_graph';
import CourseContext from '../contexts/CourseContext';

const CourseKnowledgePage = () => {
  const [graph, setGraph] = useState({ nodes: [], relationships: [] });
  const [useGraph2, setUseGraph2] = useState(true);
  const { course } = useContext(CourseContext);

  useEffect(() => {
    if (course?.name) {
      getKnowledgeGraph({ courseName: course.name }).then(setGraph);
    }
  }, [course?.name]);

  // 如果课程信息未加载，显示加载状态
  if (!course?.name) {
    return (
      <Card className="neumorphic-card" title="课程知识图谱" style={{ margin: '20px' }}>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          课程信息加载中...
        </div>
      </Card>
    );
  }

  return (
    <Card
      className="neumorphic-card"
      title="课程知识图谱"
      style={{ margin: '20px' }}
      extra={
        <div style={{ marginTop: 20 }}>
          <Button className="neumorphic-btn" onClick={() => setUseGraph2((v) => !v)}>
            {useGraph2 ? '趣味版' : '简洁版'}
          </Button>
        </div>
      }
    >
      <ResizableBox
        width="100%"
        height={500}
        minConstraints={[400, 300]}
        maxConstraints={[1200, 800]}
        resizeHandles={['se', 'e', 's']}
        style={{
          margin: '0 auto',
          padding: 12,
          borderRadius: 12,
        }}
      >
        {useGraph2 ? (
          <KnowledgeGraph2
            nodes={graph.nodes}
            relationships={graph.relationships}
            height="100%"
            width="100%"
          />
        ) : (
          <KnowledgeGraph
            nodes={graph.nodes}
            relationships={graph.relationships}
            height="100%"
            width="100%"
          />
        )}
      </ResizableBox>
    </Card>
  );
};

export default CourseKnowledgePage;
