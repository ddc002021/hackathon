import networkx as nx
from typing import Dict, Any, List

class GraphBuilder:
    """Build NetworkX graph from features"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.parsed_data = None  # Store for later retrieval
    
    def build_graph(self, feature_data: Dict[str, Any], parsed_data: Dict[str, Any]) -> nx.DiGraph:
        """Build graph from extracted features"""
        self.graph.clear()
        self.parsed_data = parsed_data
        
        # Create nodes for features
        for feature in feature_data['features']:
            self.graph.add_node(
                feature['id'],
                type='feature',
                name=feature['name'],
                description=feature['description'],
                files=feature['files'],
                functions=feature['functions'],
                modality='code'
            )
        
        # Create edges for relationships
        for rel in feature_data['relationships']:
            if self.graph.has_node(rel['source']) and self.graph.has_node(rel['target']):
                self.graph.add_edge(
                    rel['source'],
                    rel['target'],
                    relation=rel['type'],
                    description=rel.get('description', ''),
                    confidence=rel.get('confidence', 70),
                    evidence=rel.get('evidence', '')
                )
        
        return self.graph
    
    def build_unified_graph(
        self, 
        paper_nodes: List[Dict[str, Any]], 
        code_nodes: List[Dict[str, Any]], 
        cross_modal_edges: List[Dict[str, Any]],
        paper_edges: List[Dict[str, Any]] = None
    ) -> nx.DiGraph:
        """
        Build unified graph with paper + code nodes and THREE types of edges:
        1. Paper-to-paper edges (concept relationships)
        2. Code-to-code edges (feature dependencies)
        3. Cross-modal edges (paper↔code mappings)
        """
        self.graph.clear()
        
        # Add paper nodes
        for node in paper_nodes:
            self.graph.add_node(
                node['id'],
                type=node['type'],
                name=node['name'],
                description=node.get('description', ''),
                full_content=node.get('full_content', ''),
                modality='paper'
            )
        
        # Add code nodes
        for node in code_nodes:
            self.graph.add_node(
                node['id'],
                type=node.get('type', 'feature'),
                name=node['name'],
                description=node.get('description', ''),
                files=node.get('files', []),
                functions=node.get('functions', []),
                modality='code'
            )
        
        # Add paper-to-paper edges (NEW: creates graph structure within paper!)
        if paper_edges:
            for edge in paper_edges:
                if self.graph.has_node(edge['source']) and self.graph.has_node(edge['target']):
                    self.graph.add_edge(
                        edge['source'],
                        edge['target'],
                        relation=edge['type'],
                        description=edge.get('description', ''),
                        confidence=edge.get('confidence', 80),
                        evidence=edge.get('evidence', 'Paper analysis'),
                        cross_modal=False,
                        intra_paper=True  # Mark as paper-internal edge
                    )
        
        # Add cross-modal edges (paper↔code)
        for edge in cross_modal_edges:
            if self.graph.has_node(edge['source']) and self.graph.has_node(edge['target']):
                self.graph.add_edge(
                    edge['source'],
                    edge['target'],
                    relation=edge['type'],
                    description=edge.get('description', ''),
                    confidence=edge.get('confidence', 70),
                    evidence=edge.get('evidence', ''),
                    cross_modal=True,
                    intra_paper=False
                )
        
        return self.graph
    
    def get_feature_details(self, feature_id: str) -> Dict[str, Any]:
        """Get detailed information about a feature including related files and functions"""
        if not self.graph.has_node(feature_id):
            return None
        
        node_data = self.graph.nodes[feature_id]
        
        # Get function details from parsed data (only for code nodes)
        function_details = []
        is_paper_node = node_data.get('modality') == 'paper'
        
        if not is_paper_node:
            for func_name in node_data.get('functions', []):
                func_info = self._find_function_in_parsed_data(func_name)
                if func_info:
                    function_details.append(func_info)
        
        return {
            'id': feature_id,
            'name': node_data['name'],
            'description': node_data['description'],
            'files': node_data.get('files', []),
            'functions': function_details,
            'modality': node_data.get('modality', 'code'),
            'full_content': node_data.get('full_content', ''),
            'type': node_data.get('type', 'feature')
        }
    
    def _find_function_in_parsed_data(self, func_name: str) -> Dict[str, Any]:
        """Find function details in parsed data"""
        if not self.parsed_data:
            return None
        
        for file_data in self.parsed_data['files']:
            for func in file_data['functions']:
                if func['name'] == func_name:
                    return {
                        'name': func['name'],
                        'file': file_data['path'],
                        'code': func.get('code', ''),
                        'lineno': func.get('lineno', 0),
                        'args': func.get('args', [])
                    }
        return None
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'node_types': self._count_node_types(),
            'avg_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes() if self.graph.number_of_nodes() > 0 else 0
        }
    
    def _count_node_types(self) -> Dict[str, int]:
        """Count nodes by type"""
        counts = {}
        for _, data in self.graph.nodes(data=True):
            node_type = data.get('type', 'unknown')
            counts[node_type] = counts.get(node_type, 0) + 1
        return counts
    
    def export_for_visualization(self) -> Dict[str, Any]:
        """Export graph in React Flow format (Semantic View - supports paper + code)"""
        nodes = []
        edges = []
        
        # Separate paper and code nodes for better layout
        paper_nodes = []
        code_nodes = []
        
        for node_id, data in self.graph.nodes(data=True):
            if data.get('modality') == 'paper':
                paper_nodes.append((node_id, data))
            else:
                code_nodes.append((node_id, data))
        
        # Position calculation - paper on left, code on right
        if self.graph.number_of_nodes() > 0:
            pos = {}
            
            # Layout paper nodes on the left (closer together)
            for idx, (node_id, data) in enumerate(paper_nodes):
                pos[node_id] = (-200, idx * 80)
            
            # Layout code nodes on the right (closer together)
            for idx, (node_id, data) in enumerate(code_nodes):
                pos[node_id] = (200, idx * 80)
        else:
            pos = {}
        
        # Create node visualizations
        for node_id, data in self.graph.nodes(data=True):
            x, y = pos.get(node_id, (0, 0))
            modality = data.get('modality', 'code')
            
            nodes.append({
                'id': node_id,
                'data': {
                    'label': data.get('name', node_id),
                    'description': data.get('description', ''),
                    'type': data.get('type', 'feature'),
                    'files': data.get('files', []),
                    'functions': data.get('functions', []),
                    'full_content': data.get('full_content', ''),
                    'modality': modality,
                    'view': 'features'
                },
                'position': {'x': float(x), 'y': float(y)},
                'type': 'default'
            })
        
        # Create edge visualizations
        for source, target, data in self.graph.edges(data=True):
            relation_type = data.get('relation', '')
            is_cross_modal = data.get('cross_modal', False)
            is_intra_paper = data.get('intra_paper', False)
            
            edges.append({
                'id': f"{source}-{target}",
                'source': source,
                'target': target,
                'label': relation_type,
                'description': data.get('description', ''),
                'confidence': data.get('confidence', 70),
                'cross_modal': is_cross_modal,
                'intra_paper': is_intra_paper,  # NEW: identify paper-to-paper edges
                'animated': is_cross_modal or relation_type in ['implements', 'describes']
            })
        
        return {'nodes': nodes, 'edges': edges}

