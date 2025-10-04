import React, { useCallback, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import PathVisualization from './PathVisualization';

const nodeColor = (node) => {
  // Color based on modality (paper vs code)
  if (node.data.modality === 'paper') {
    // Paper nodes - shades of orange/amber
    switch (node.data.type) {
      case 'paper':
        return '#f59e0b'; // amber - root paper
      case 'paper_section':
        return '#fb923c'; // orange - sections
      case 'paper_algorithm':
        return '#f97316'; // deep orange - algorithms
      default:
        return '#fdba74'; // light orange
    }
  }
  
  // Color based on view type
  if (node.data.view === 'dependencies') {
    // In dependency view, color by dependency count
    const totalDeps = (node.data.in_degree || 0) + (node.data.out_degree || 0);
    if (totalDeps > 4) return '#ef4444'; // red - highly coupled
    if (totalDeps > 2) return '#f59e0b'; // orange - moderate
    return '#10b981'; // green - low coupling
  }
  
  // Code nodes - shades of purple/blue
  switch (node.data.type) {
    case 'feature':
      return '#8b5cf6'; // purple for features
    case 'dependency':
      return '#3b82f6'; // blue for dependencies
    case 'file':
      return '#60a5fa';
    case 'function':
      return '#34d399';
    case 'class':
      return '#fbbf24';
    case 'module':
      return '#a78bfa';
    default:
      return '#9ca3af';
  }
};

export default function GraphView({ initialNodes, initialEdges, highlightedNodes, highlightedPaths, onFeatureClick, currentView }) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Update nodes when initialNodes change (view switch) - preserve highlighting
  React.useEffect(() => {
    setIsTransitioning(true);
    
    const nodesWithHighlighting = initialNodes.map((node) => ({
      ...node,
      style: {
        ...node.style,
        backgroundColor: highlightedNodes.includes(node.id) ? '#fbbf24' : nodeColor(node),
        border: highlightedNodes.includes(node.id) ? '3px solid #f59e0b' : '2px solid #000',
        cursor: isTransitioning ? 'wait' : (node.data.type === 'feature' ? 'pointer' : 'default'),
        padding: '12px',
        borderRadius: '8px',
        fontSize: '14px',
        fontWeight: '600',
        boxShadow: highlightedNodes.includes(node.id) ? '0 0 20px rgba(251, 191, 36, 0.6)' : 'none',
        transition: 'all 0.3s ease',
        pointerEvents: isTransitioning ? 'none' : 'auto',
      },
    }));
    setNodes(nodesWithHighlighting);
    
    // Re-enable clicks after transition completes
    const timer = setTimeout(() => setIsTransitioning(false), 350);
    return () => clearTimeout(timer);
  }, [initialNodes, highlightedNodes]);

  // Update edges when initialEdges change (view switch) - preserve path highlighting
  React.useEffect(() => {
    // Build set of edges that are in paths
    const pathEdgeSet = new Set();
    
    if (highlightedPaths && highlightedPaths.length > 0) {
      highlightedPaths.forEach(path => {
        if (path.nodes && path.nodes.length > 1) {
          for (let i = 0; i < path.nodes.length - 1; i++) {
            const source = path.nodes[i];
            const target = path.nodes[i + 1];
            pathEdgeSet.add(`${source}-${target}`);
          }
        }
      });
    }

    // Apply highlighting to edges
    const edgesWithHighlighting = initialEdges.map((edge) => {
      const isInPath = pathEdgeSet.has(edge.id);
      
      return {
        ...edge,
        animated: isInPath || edge.animated,
        style: {
          ...edge.style,
          stroke: isInPath ? '#f59e0b' : (edge.cross_modal ? '#3b82f6' : (edge.intra_paper ? '#fb923c' : '#94a3b8')),
          strokeWidth: isInPath ? 3 : 2,
          opacity: highlightedPaths && highlightedPaths.length > 0 ? (isInPath ? 1 : 0.3) : 1,
        },
        markerEnd: {
          type: 'arrowclosed',
          width: isInPath ? 25 : 20,
          height: isInPath ? 25 : 20,
          color: isInPath ? '#f59e0b' : undefined,
        },
        label: isInPath && edge.label ? edge.label : undefined,
        labelStyle: isInPath ? {
          fill: '#f59e0b',
          fontWeight: 700,
          fontSize: 14,
        } : edge.labelStyle,
      };
    });
    
    setEdges(edgesWithHighlighting);
  }, [initialEdges, highlightedPaths, setEdges]);

  // Handle node click - now for features
  const onNodeClick = useCallback((event, node) => {
    if (isTransitioning) {
      return; // Prevent clicks during transition
    }
    if (node.data.type === 'feature' || node.data.view === 'features') {
      onFeatureClick(node.id);
    }
  }, [onFeatureClick, isTransitioning]);


  return (
    <div style={{ width: '100%', height: '600px', position: 'relative' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{
          padding: 0.2,
          minZoom: 0.5,
          maxZoom: 1.5
        }}
        defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{
          type: 'smoothstep',
          animated: false,
          markerEnd: {
            type: 'arrowclosed',
            width: 20,
            height: 20
          }
        }}
        proOptions={{ hideAttribution: true }}
      >
        <Controls />
        <MiniMap nodeColor={nodeColor} pannable zoomable />
        <Background variant="dots" gap={16} size={1} />
      </ReactFlow>

      {/* Path Visualization Overlay */}
      {highlightedPaths && highlightedPaths.length > 0 && (
        <PathVisualization paths={highlightedPaths} queryType={currentView} />
      )}
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white px-4 py-3 border border-gray-300 text-xs max-w-xs shadow-sm">
        {currentView === 'dependencies' ? (
          <>
            <span className="font-medium text-gray-900">Coupling Levels:</span>
            <div className="mt-1 space-y-1">
              <div><span className="inline-block w-2 h-2 rounded-full bg-green-600 mr-2"></span>Low</div>
              <div><span className="inline-block w-2 h-2 rounded-full bg-orange-500 mr-2"></span>Medium</div>
              <div><span className="inline-block w-2 h-2 rounded-full bg-red-600 mr-2"></span>High</div>
            </div>
          </>
        ) : (
          <>
            <span className="font-medium text-gray-900">Cross-Modal Graph:</span>
            <div className="mt-2 space-y-1.5">
              <div className="flex items-start">
                <span className="inline-block w-2 h-2 rounded-full bg-orange-500 mr-2 mt-1"></span>
                <span>Paper Sections/Concepts</span>
              </div>
              <div className="flex items-start">
                <span className="inline-block w-2 h-2 rounded-full bg-purple-600 mr-2 mt-1"></span>
                <span>Code Features/Implementations</span>
              </div>
            </div>
            <p className="mt-3 text-gray-600 text-xs">
              Click paper nodes to see full section text. Edges show which code implements which paper concept.
            </p>
          </>
        )}
      </div>
    </div>
  );
}

