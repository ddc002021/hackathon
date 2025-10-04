import React, { useMemo } from 'react';
import ReactFlow, { 
  Background, 
  Controls,
  MiniMap
} from 'reactflow';
import 'reactflow/dist/style.css';

const getNodeColor = (type) => {
  switch (type) {
    case 'start':
      return '#10b981'; // green
    case 'argument':
      return '#3b82f6'; // blue
    case 'assignment':
      return '#8b5cf6'; // purple
    case 'condition':
      return '#f59e0b'; // amber
    case 'loop':
      return '#ec4899'; // pink
    case 'call':
      return '#06b6d4'; // cyan
    case 'operation':
      return '#6366f1'; // indigo
    case 'return':
      return '#10b981'; // green
    case 'error':
      return '#ef4444'; // red
    default:
      return '#9ca3af'; // gray
  }
};

const getEdgeColor = (type) => {
  switch (type) {
    case 'input':
      return '#3b82f6';
    case 'uses':
      return '#8b5cf6';
    case 'returns':
      return '#10b981';
    case 'condition_check':
      return '#f59e0b';
    case 'error':
      return '#ef4444';
    default:
      return '#9ca3af';
  }
};

export default function ExecutionTraceGraph({ traceData }) {
  const { nodes: traceNodes, edges: traceEdges } = useMemo(() => {
    if (!traceData || !traceData.nodes) {
      return { nodes: [], edges: [] };
    }

    // Sort nodes by step number for vertical layout
    const sortedNodes = [...traceData.nodes].sort((a, b) => {
      const stepA = a.metadata?.step !== undefined ? a.metadata.step : 999;
      const stepB = b.metadata?.step !== undefined ? b.metadata.step : 999;
      return stepA - stepB;
    });

    // Convert trace nodes to React Flow format with vertical flow layout
    const nodes = sortedNodes.map((node, index) => ({
      id: node.id,
      type: 'default',
      data: {
        label: (
          <div className="text-center px-2">
            <div className="font-bold text-sm mb-1">{node.label}</div>
            {node.value && node.value !== 'null' && (
              <div className="text-xs mt-1 max-w-[200px] break-words">
                {node.value}
              </div>
            )}
          </div>
        )
      },
      // Vertical flow layout with better spacing
      position: { x: 50, y: index * 180 },
      style: {
        background: getNodeColor(node.type),
        color: 'white',
        border: '3px solid rgba(255,255,255,0.5)',
        borderRadius: '12px',
        padding: '12px 16px',
        fontSize: '13px',
        minWidth: '200px',
        maxWidth: '280px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
      }
    }));

    // Convert trace edges to React Flow format
    const edges = traceData.edges.map((edge, index) => ({
      id: `e${index}`,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep',
      animated: edge.type === 'then',
      label: edge.type === 'then' ? '↓' : edge.type,
      style: { 
        stroke: getEdgeColor(edge.type), 
        strokeWidth: 3 
      },
      labelStyle: { 
        fill: '#374151',
        fontWeight: 700, 
        fontSize: 14,
        background: 'white',
        padding: '2px 6px',
        borderRadius: '4px'
      },
      markerEnd: {
        type: 'arrowclosed',
        width: 20,
        height: 20,
        color: getEdgeColor(edge.type)
      }
    }));

    return { nodes, edges };
  }, [traceData]);

  if (!traceData || !traceData.nodes || traceData.nodes.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        <p>No execution trace available</p>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '500px' }}>
      <ReactFlow
        nodes={traceNodes}
        edges={traceEdges}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        attributionPosition="bottom-left"
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
        nodesDraggable={true}
        nodesConnectable={false}
        elementsSelectable={true}
      >
        <Background color="#f3f4f6" gap={20} size={1} />
        <Controls />
        <MiniMap
          nodeColor={(node) => node.style.background}
          maskColor="rgba(0, 0, 0, 0.05)"
          style={{
            background: '#f9fafb',
            border: '1px solid #e5e7eb'
          }}
        />
      </ReactFlow>
    </div>
  );
}

