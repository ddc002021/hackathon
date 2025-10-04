import networkx as nx
from typing import Dict, Any, List
from .llm_analyzer import LLMAnalyzer

class QueryEngine:
    """Process natural language queries against the code graph"""
    
    def __init__(self, graph: nx.DiGraph, llm_analyzer: LLMAnalyzer):
        self.graph = graph
        self.llm = llm_analyzer
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Main query processing pipeline"""
        
        # Extract intent using LLM
        intent_data = self.llm.extract_intent(query)
        
        # Find relevant subgraph
        relevant_subgraph = self._find_relevant_subgraph(
            intent_data['entities'],
            intent_data['scope']
        )
        
        # Generate answer using LLM
        answer = self.llm.answer_query(query, relevant_subgraph)
        
        # Get highlighted nodes for visualization
        highlighted_nodes = self._get_highlighted_nodes(relevant_subgraph)
        
        return {
            'query': query,
            'answer': answer,
            'intent': intent_data,
            'highlighted_nodes': highlighted_nodes,
            'subgraph': relevant_subgraph
        }
    
    def _find_relevant_subgraph(self, entities: List[str], scope: str) -> Dict[str, Any]:
        """Extract relevant portion of graph"""
        relevant_nodes = []
        
        # Find nodes matching entities
        for node, data in self.graph.nodes(data=True):
            node_name = data.get('name', '').lower()
            if any(entity.lower() in node_name for entity in entities):
                relevant_nodes.append(node)
        
        # If no specific entities, get central nodes
        if not relevant_nodes and self.graph.number_of_nodes() > 0:
            # Get nodes with highest degree (most connected)
            degree_dict = dict(self.graph.degree())
            sorted_nodes = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)
            relevant_nodes = [node for node, _ in sorted_nodes[:5]]
        
        # Build subgraph
        subgraph_nodes = set(relevant_nodes)
        for node in relevant_nodes:
            # Add neighbors (1-hop)
            subgraph_nodes.update(self.graph.neighbors(node))
            subgraph_nodes.update(self.graph.predecessors(node))
        
        # Extract subgraph data
        subgraph_data = {
            'nodes': [],
            'edges': []
        }
        
        for node in list(subgraph_nodes)[:20]:  # Limit to 20 nodes
            if self.graph.has_node(node):
                subgraph_data['nodes'].append({
                    'id': node,
                    'data': dict(self.graph.nodes[node])
                })
        
        for source, target in self.graph.edges():
            if source in subgraph_nodes and target in subgraph_nodes:
                subgraph_data['edges'].append({
                    'source': source,
                    'target': target,
                    'relation': self.graph.edges[source, target].get('relation', '')
                })
        
        return subgraph_data
    
    def _get_highlighted_nodes(self, subgraph: Dict[str, Any]) -> List[str]:
        """Get list of node IDs to highlight"""
        return [node['id'] for node in subgraph.get('nodes', [])]
    
    def find_path(self, source: str, target: str) -> List[str]:
        """Find path between two nodes"""
        try:
            # Find nodes by name
            source_node = self._find_node_by_name(source)
            target_node = self._find_node_by_name(target)
            
            if source_node and target_node:
                path = nx.shortest_path(self.graph, source_node, target_node)
                return path
        except nx.NetworkXNoPath:
            return []
        
        return []
    
    def _find_node_by_name(self, name: str) -> str:
        """Find node ID by name"""
        name_lower = name.lower()
        for node, data in self.graph.nodes(data=True):
            if data.get('name', '').lower() == name_lower:
                return node
        return None

