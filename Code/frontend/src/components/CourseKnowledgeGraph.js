import React, { useEffect, useState } from 'react';
import { Card, Spin, Empty, Button, Space, Tooltip, message } from 'antd';
import { ExpandAltOutlined, CompressOutlined, ReloadOutlined } from '@ant-design/icons';
import KnowledgeGraph from './KnowledgeGraph';
import { searchKnowledgeGraphByField, getNodeNeighbors } from '../service/knowledge_graph';

const CourseKnowledgeGraph = ({ courseName, height = 480 }) => {
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [expandedNodeId, setExpandedNodeId] = useState(null);
  const [depth, setDepth] = useState(1);
  const [error, setError] = useState(null);

  const fetchGraphData = async () => {
    if (!courseName) {
      console.log('No courseName provided, skipping fetch');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      console.log('Fetching knowledge graph for course:', courseName);
      
      const response = await searchKnowledgeGraphByField({
        field: 'course',
        value: courseName
      });

      console.log('Knowledge graph API response:', response);

      if (response && response.result) {  // 检查 response 和 result 是否存在
        // 转换数据格式以适配KnowledgeGraph组件
        const nodes = response.result.nodes.map(node => ({
          id: node.id.toString(), // 确保id是字符串类型
          label: node.properties.name,
          group: node.properties.entity_type === 'Concept' ? 0 : 1,
          title: `${node.properties.name}\n类型: ${node.properties.entity_type}`
        }));

        // 如果没有关系数据，创建一些基于节点位置的默认关系
        let edges = [];
        if (response.result.relationships && response.result.relationships.length > 0) {
          edges = response.result.relationships.map(rel => ({
            from: rel.source.toString(),
            to: rel.target.toString(),
            label: rel.type
          }));
        } else {
          // 创建一个简单的环形布局的关系
          for (let i = 0; i < nodes.length - 1; i++) {
            edges.push({
              from: nodes[i].id,
              to: nodes[i + 1].id,
              label: '相关'
            });
          }
          // 可选：连接最后一个节点和第一个节点，形成完整的环
          if (nodes.length > 2) {
            edges.push({
              from: nodes[nodes.length - 1].id,
              to: nodes[0].id,
              label: '相关'
            });
          }
        }

        console.log('Processed graph data:', { nodes, edges });

        if (nodes.length === 0) {
          console.log('No nodes found in the response');
          setError('该课程暂无知识图谱数据');
        } else {
          setGraphData({ nodes, edges });
        }
      } else {
        console.error('Invalid API response format:', response);
        setError('获取知识图谱失败：响应格式错误');
      }
    } catch (error) {
      console.error('Failed to fetch knowledge graph:', error);
      setError('获取知识图谱数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('CourseKnowledgeGraph mounted/updated with courseName:', courseName);
    fetchGraphData();
  }, [courseName]);

  const handleExpand = async (nodeId) => {
    if (!nodeId) return;
    
    try {
      setLoading(true);
      console.log('Expanding node:', nodeId);
      
      const response = await getNodeNeighbors({
        nodeId: parseInt(nodeId),
        depth,
      });

      console.log('Node neighbors response:', response);

      if (response && response.result) {  // 检查 response 和 result 是否存在
        const newNodes = response.result.nodes.map(node => ({
          id: node.id.toString(),
          label: node.properties.name,
          group: node.properties.entity_type === 'Concept' ? 0 : 1,
          title: `${node.properties.name}\n类型: ${node.properties.entity_type}`
        }));

        const newEdges = response.result.relationships.map(rel => ({
          from: rel.source.toString(),
          to: rel.target.toString(),
          label: rel.type
        }));

        console.log('New nodes and edges:', { newNodes, newEdges });

        // 合并新旧数据，去重
        const existingNodeIds = new Set(graphData.nodes.map(n => n.id));
        const existingEdgeKeys = new Set(graphData.edges.map(e => `${e.from}-${e.to}`));

        const uniqueNewNodes = newNodes.filter(node => !existingNodeIds.has(node.id));
        const uniqueNewEdges = newEdges.filter(edge => !existingEdgeKeys.has(`${edge.from}-${edge.to}`));

        setGraphData(prev => ({
          nodes: [...prev.nodes, ...uniqueNewNodes],
          edges: [...prev.edges, ...uniqueNewEdges]
        }));

        setExpandedNodeId(nodeId);
      } else {
        console.error('Invalid API response format:', response);
        message.error('展开节点失败：响应格式错误');
      }
    } catch (error) {
      console.error('Error expanding node:', error);
      message.error('展开节点时发生错误');
    } finally {
      setLoading(false);
    }
  };

  const handleDepthChange = () => {
    setDepth(depth === 1 ? 2 : 1);
    if (expandedNodeId) {
      handleExpand(expandedNodeId);
    }
  };

  const handleRefresh = () => {
    fetchGraphData();
  };

  if (!courseName) {
    return <Empty description="请选择一个课程" />;
  }

  if (error) {
    return (
      <Card>
        <Empty
          description={error}
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button type="primary" onClick={handleRefresh} icon={<ReloadOutlined />}>
            重试
          </Button>
        </Empty>
      </Card>
    );
  }

  return (
    <Card
      title={`${courseName} 知识图谱`}
      extra={
        <Space>
          <Tooltip title={depth === 1 ? "展开更多层级" : "减少展开层级"}>
            <Button
              icon={depth === 1 ? <ExpandAltOutlined /> : <CompressOutlined />}
              onClick={handleDepthChange}
            />
          </Tooltip>
          <Tooltip title="刷新">
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={loading}
            />
          </Tooltip>
        </Space>
      }
    >
      <Spin spinning={loading}>
        {graphData.nodes.length > 0 ? (
          <KnowledgeGraph
            nodes={graphData.nodes}
            edges={graphData.edges}
            height={height}
            onNodeClick={handleExpand}
            selectedNodeId={expandedNodeId}
          />
        ) : (
          <Empty description="暂无知识图谱数据" />
        )}
      </Spin>
    </Card>
  );
};

export default CourseKnowledgeGraph; 