import React, { useState, useMemo, useCallback } from 'react';
import Tree from 'react-d3-tree';
import "../css/kg.css"

// 简洁版知识图谱
const importanceColorMap = {
  High: '#f08f92',
  Medium: '#9cbedb',
  Low: '#a9d5a5'
};

const getNodeColor = (importance) => importanceColorMap[importance] || '#bdbdbd';


function estimateTextWidth(text, fontSize = 12) {
  let width = 0;
  for (let ch of text) {
    // 中文字符范围
    if (/[\u4e00-\u9fa5]/.test(ch)) {
      width += fontSize * 1.2;
    } else {
      width += fontSize * 0.6;
    }
  }
  return width;
}

const KnowledgeGraph2 = ({ nodes = [], relationships = [], height = 480 }) => {
  const [translate, setTranslate] = useState({ x: 0, y: 0 });
  const [hoveredNodeId, setHoveredNodeId] = useState(null);

  const containerRef = useCallback((containerElem) => {
    if (containerElem) {
      const { width } = containerElem.getBoundingClientRect();
      setTranslate({ x: width / 2, y: 50 });
    }
  }, []);

  const fontSize = 12;
  const minOffset = 30;
  const maxOffset = 120;

  function calcLabelOffset(name) {
    return Math.max(minOffset, Math.min(maxOffset, name.length * fontSize * 0.6 + 30));
  }

  function addOffsets(node, parentLabelOffset = 0) {
    node.labelOffset = calcLabelOffset(node.name);
    node.parentLabelOffset = parentLabelOffset;
    if (node.children && node.children.length > 0) {
      node.children.forEach(child => addOffsets(child, node.labelOffset));
    }
  }

  const transformData = useMemo(() => {
    if (!nodes.length) return {
      name: 'No data available',
      attributes: { importance: 'None' },
      nodeSvgShape: {
        shape: 'circle',
        shapeProps: {
          r: 10,
          fill: '#bdbdbd'
        }
      }
    };

    const rootNode = nodes.find(n => n.properties?.entity_type === 'CourseRoot') || nodes[0];
    console.log("nodes", nodes);
    console.log("rootNode", rootNode);
    const nodeMap = {};

    // Create all nodes first
    nodes.forEach(n => {
        nodeMap[n.id] = {
          id: n.id,
          name: n.properties?.name || `Node ${n.id}`,
          attributes: {
            importance: n.properties?.importance || 'None',
            description: n.properties?.description || ''
          },
          nodeSvgShape: {
            shape: 'circle',
            shapeProps: {
              r: n.properties?.entity_type === 'CourseRoot' ? 20 : 15,
              fill: getNodeColor(n.properties?.importance),
              stroke: '#999',
              strokeWidth: 1
            }
          },
          children: [] // 保证每个节点都有children
        };
      });

    // Build hierarchy
    relationships.forEach(rel => {
        if (nodeMap[rel.source] && nodeMap[rel.target]) {
            nodeMap[rel.source].children.push(nodeMap[rel.target]);
        }
    });

    const tree = nodeMap[rootNode.id] || {
      name: 'Invalid data structure',
      attributes: { importance: 'None' },
      nodeSvgShape: {
        shape: 'circle',
        shapeProps: {
          r: 10,
          fill: '#bdbdbd'
        }
      }
    };

    addOffsets(tree, 0);
    console.log(nodeMap)
    return tree;  
  }, [nodes, relationships]);

  
   
  return (
    <div 
      className="neumorphic-item"
      ref={containerRef}
      style={{ 
        width: '100%', 
        height,
        background: 'transparent'
      }}
    >
      <Tree
        data={transformData}
        orientation="horizontal"
        translate={translate}
        pathFunc="curved"
        zoomable={true}
        draggable={true}
        initialDepth={1}
        nodeSize={{ x: 200, y: 100 }}
        separation={{ siblings: 1, nonSiblings: 1 }}
        renderCustomNodeElement={({ nodeDatum, toggleNode }) => {
          const isHovered = hoveredNodeId === nodeDatum.id;
          const hasHiddenChildren = nodeDatum._children && nodeDatum._children.length > 0;
          const hasVisibleChildren = nodeDatum.children && nodeDatum.children.length > 0;
          const isExpandable = hasHiddenChildren || hasVisibleChildren;
          const fontSize = 12;
          const textWidth = estimateTextWidth(nodeDatum.name, fontSize);
        
          return (
            <g g className={`animated-node depth-${nodeDatum.depth}`}>
              {/* 荧光笔高亮 */}
              <rect
                x={-textWidth / 2 - 6}
                y={-23}
                width={textWidth + 12}
                height={18}
                rx={4}
                fill={getNodeColor(nodeDatum.attributes.importance)}
                opacity={0.5}
                stroke="none"
              />
              <text
                x={0}
                y={-10}
                textAnchor="middle"
                fill="#333"
                stroke="none"
                fontSize={fontSize}
                onClick={isExpandable ? toggleNode : undefined}
                style={{ cursor: isExpandable ? 'pointer' : 'default' }}
              >
                {nodeDatum.name}
              </text>
              {/* 统一展开符号 */}
              {isExpandable && (
                <g>
                  <circle cx={0} cy={12} r={8} fill="#fff" stroke="#888" strokeWidth={1}/>
                  <polygon points="-4,10 4,10 0,16" fill="#333" />
                </g>
              )}
              {isHovered && (
                <foreignObject x={10} y={-30} width={180} height={60} style={{ pointerEvents: 'none' }}>
                  <div style={{ background: 'rgba(255,255,255,0.95)', border: '1px solid #ccc', borderRadius: 6, padding: 6, fontSize: 12, color: '#333', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
                    {Object.entries(nodeDatum.attributes || {}).map(([k, v]) => (
                      <div key={k}><b>{k}:</b> {v}</div>
                    ))}
        </div>
                </foreignObject>
              )}
            </g>
          );
        }}
      />
      </div>
  );
};

export default KnowledgeGraph2;