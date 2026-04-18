import React, { useEffect, useRef, useState } from 'react';

const importanceColorMap = {
  High: '#f08f92',
  Medium: '#9cbedb',
  Low: '#a9d5a5'
};

function getNodeColor(idx, importance) {
  if (importance && importanceColorMap[importance]) {
    return importanceColorMap[importance];
  }
  return '#bdbdbd';
}

function buildNodeTooltip(properties = {}) {
  const fields = ['name', 'content', 'category', 'importance', 'description', 'entity_type'];
  return fields
    .filter(k => properties[k] && properties[k] !== '')
    .map(k => `${k}: ${properties[k]}`)
    .join('\n');
}

function buildEdgeTooltip(properties = {}) {
  const fields = ['direction', 'strength', 'description'];
  return fields
    .filter(k => properties[k] && properties[k] !== '')
    .map(k => `${k}: ${properties[k]}`)
    .join('\n');
}

function buildVisData(nodes = [], relationships = [], allEdges = [], visibleNodeIds = []) {
  const visNodes = nodes.map((n, i) => {
    const isCourseRoot = n.properties?.entity_type === 'CourseRoot';
    const importance = n.properties?.importance;
    const label = n.properties?.name || n.properties?.entity_id || `节点${n.id}`;
    const labelLength = label.length;
    const baseSize = isCourseRoot ? 120 : 100;
    const dynamicSize = baseSize + labelLength * 8;

    const neighborEdges = allEdges.filter(e => e.source === n.id || e.target === n.id);
    const neighborNodeIds = neighborEdges.map(e => e.source === n.id ? e.target : e.source);
    const hiddenNeighborIds = neighborNodeIds.filter(id => !visibleNodeIds.includes(id));
    const isExpandable = hiddenNeighborIds.length > 0;

    return {
      id: n.id,
      label,
      group: n.properties?.entity_type || n.labels?.[0] || 'default',
      title: buildNodeTooltip(n.properties),
      color: {
        background: getNodeColor(i, importance),
        border: 'rgba(0,0,0,0)',
        // 👇 彻底禁用默认 highlight 样式
        highlight: {
          background: getNodeColor(i, importance),
          border: 'rgba(0,0,0,0)'
        },
        hover: {
          background: getNodeColor(i, importance),
          border: 'rgba(0,0,0,0)'
        }
      },
      font: {
        color: '#000',
        size: isCourseRoot ? 36 : 28,
        face: 'PingFang SC, Microsoft YaHei, Arial',
        bold: 'bold',  // 修改为字符串 'bold'
        multi: true
      },
      shape: 'ellipse',
      borderWidth: 0,
      size: dynamicSize,
      // 去除 shadow 光晕
      originalColor: getNodeColor(i, importance),
      isExpandable
    };
  });

  const visEdges = relationships.map((e,index) => ({
    id: `e${index+1}`,
    from: e.source,
    to: e.target,
    label: e.type,
    arrows: 'to',
    color: { color: '#bdbdbd' },
    font: { color: '#555', size: 14, align: 'middle' },
    title: buildEdgeTooltip(e.properties)
  }));

  return { nodes: visNodes, edges: visEdges };
}

const KnowledgeGraph = ({ nodes = [], relationships = [], height = 480 }) => {
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  // const [visibleNodeIds, setVisibleNodeIds] = useState([]);
  // const [visibleEdgeIds, setVisibleEdgeIds] = useState([]);
  // const [allNodes, setAllNodes] = useState([]);
  // const [allEdges, setAllEdges] = useState([]);
  const nodeColorCache = useRef({});

  // useEffect(() => {
  //   setAllNodes(nodes);
  //   setAllEdges(relationships);
  //   const rootNodes = nodes.filter(n => n.properties?.entity_type === 'CourseRoot');
  //   setVisibleNodeIds(rootNodes.map(n => n.id));
  //   setVisibleEdgeIds([]);
  // }, [nodes, relationships]);

  // const visibleNodes = allNodes.filter(n => visibleNodeIds.includes(n.id));
  // const visibleEdges = allEdges.filter(e => visibleEdgeIds.includes(`e${e.id}`));

  useEffect(() => {
    if (!containerRef.current) return;
    if (networkRef.current) networkRef.current.destroy();
    containerRef.current.innerHTML = '';

    const vis = require('vis-network/standalone');
    // const { nodes: visNodes, edges: visEdges } = buildVisData(visibleNodes, visibleEdges, allEdges, visibleNodeIds);
    const { nodes: visNodes, edges: visEdges } = buildVisData(nodes, relationships, relationships, nodes.map(n => n.id));
    const network = new vis.Network(containerRef.current, {
      nodes: visNodes,
      edges: visEdges
    }, {
      nodes: {
        shape: 'ellipse',
        font: { color: '#000', size: 20, face: 'PingFang SC, Microsoft YaHei, Arial', bold: 'bold' }
      },
      edges: {
        width: 3,
        color: { color: '#448dd0' },
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { color: '#555', size: 14, align: 'middle' }
      },
      layout: {
        improvedLayout: true,
        hierarchical: false
      },
      physics: {
        enabled: true,
        barnesHut: { gravitationalConstant: -30000, springLength: 150 }
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        dragNodes: true,
        dragView: true,
        zoomView: true
      }
    });

    networkRef.current = network;

    // 悬停时手动设置颜色（禁用默认样式）
    network.on('hoverNode', function (params) {
      const nodeId = params.node;
      const node = network.body.nodes[nodeId];
      const isExpandable = visNodes.find(n => n.id === nodeId)?.isExpandable;
      nodeColorCache.current[nodeId] = node.options.color.background;

      const hoverColor = isExpandable ? '#ff6b6b' : '#95a5a6';

      node.setOptions({
        color: { background: hoverColor, border: 'rgba(0,0,0,0)' }
      });
    });

    network.on('blurNode', function (params) {
      const nodeId = params.node;
      const original = nodeColorCache.current[nodeId];
      if (original) {
        network.body.nodes[nodeId].setOptions({
          color: { background: original, border: 'rgba(0,0,0,0)' }
        });
      }
    });
  
  //   // 点击展开邻居
  //   network.on('click', function (params) {
  //     if (params.nodes && params.nodes.length > 0) {
  //       const clickedId = params.nodes[0];
  //       const neighborEdges = allEdges.filter(e => e.source === clickedId || e.target === clickedId);
  //       const neighborNodeIds = neighborEdges.map(e => e.source === clickedId ? e.target : e.source);
  //       setVisibleNodeIds(prev => Array.from(new Set([...prev, ...neighborNodeIds, clickedId])));
  //       setVisibleEdgeIds(prev => Array.from(new Set([...prev, ...neighborEdges.map(e => `e${e.id}`)])));
  //     }
  //   });
  // }, [visibleNodes, visibleEdges, allEdges, visibleNodeIds]);
  }, [nodes, relationships]);

  return (
    <div style={{ position: 'relative', width: '100%', height }}>
      <div
        className="neumorphic-item"
        ref={containerRef}
        style={{
          width: '100%',
          height,
          background: 'transparent'
        }}
      />
    </div>
  );
};

export default KnowledgeGraph;
