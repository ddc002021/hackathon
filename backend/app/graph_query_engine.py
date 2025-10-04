"""
Graph-Powered Query Engine - Leverages graph structure for intelligent reasoning
This is the CORE of the hackathon demo - shows graph's value!
"""

import networkx as nx
from typing import Dict, Any, List, Tuple, Optional
from .llm_analyzer import LLMAnalyzer
import logging

logger = logging.getLogger(__name__)


class GraphQueryEngine:
    """
    Advanced query engine that ACTUALLY USES THE GRAPH STRUCTURE.
    Implements graph algorithms for reasoning, not just keyword matching.
    """
    
    def __init__(self, graph: nx.DiGraph, llm_analyzer: LLMAnalyzer):
        self.graph = graph
        self.llm = llm_analyzer
        
        # Query type classifiers (patterns)
        self.query_types = {
            'path': ['how', 'implemented', 'realize', 'from paper to code', 'chain'],
            'dependency': ['depends', 'requires', 'needs', 'prerequisite', 'based on'],
            'gap': ['missing', 'not implemented', 'gaps', 'lacking', 'unimplemented'],
            'impact': ['affect', 'modify', 'change', 'impact', 'downstream', 'breaks'],
            'summary': ['summarize', 'overview', 'explain', 'architecture', 'structure'],
            'find': ['where', 'locate', 'find', 'show me', 'which files'],
            'related': ['related to', 'connected to', 'associated with', 'linked']
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main query processing - uses graph algorithms based on query type
        """
        logger.info(f"Processing graph-based query: {query}")
        
        # Classify query type
        query_type = self._classify_query(query)
        logger.info(f"   Query type: {query_type}")
        
        # Extract entities (nodes to focus on)
        entities = self._extract_entities(query)
        logger.info(f"   Entities: {entities}")
        
        # Route to appropriate graph algorithm
        if query_type == 'path':
            result = self._handle_path_query(query, entities)
        elif query_type == 'dependency':
            result = self._handle_dependency_query(query, entities)
        elif query_type == 'gap':
            result = self._handle_gap_query(query, entities)
        elif query_type == 'impact':
            result = self._handle_impact_query(query, entities)
        elif query_type == 'summary':
            result = self._handle_summary_query(query, entities)
        elif query_type == 'find':
            result = self._handle_find_query(query, entities)
        else:  # related
            result = self._handle_related_query(query, entities)
        
        # Enhance answer with LLM
        enhanced_answer = self._enhance_with_llm(query, result)
        
        return {
            'query': query,
            'query_type': query_type,
            'answer': enhanced_answer,
            'graph_evidence': result,
            'highlighted_nodes': result.get('nodes', []),
            'paths': result.get('paths', [])
        }
    
    def _classify_query(self, query: str) -> str:
        """Classify query type based on keywords"""
        query_lower = query.lower()
        
        for qtype, keywords in self.query_types.items():
            if any(keyword in query_lower for keyword in keywords):
                return qtype
        
        return 'related'  # default
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract entity names from query"""
        # Simple approach: look for capitalized words or quoted strings
        import re
        
        entities = []
        
        # Find quoted strings
        quoted = re.findall(r'"([^"]+)"', query)
        entities.extend(quoted)
        
        # Find multi-word capitalized phrases
        cap_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        entities.extend(cap_phrases)
        
        # Find nodes whose names appear in query
        for node, data in self.graph.nodes(data=True):
            name = data.get('name', '')
            if name and name.lower() in query.lower():
                entities.append(name)
        
        return list(set(entities))[:5]  # Limit to 5 entities
    
    def _handle_path_query(self, query: str, entities: List[str]) -> Dict[str, Any]:
        """
        Handle path-finding queries: "How is X implemented?"
        Uses shortest path algorithms
        """
        logger.info("   Running path-finding algorithm")
        
        # Find source (paper) and target (code) nodes
        paper_nodes = self._find_nodes_by_entities(entities, modality='paper')
        code_nodes = self._find_nodes_by_entities(entities, modality='code')
        
        paths_found = []
        nodes_in_paths = set()
        
        # Try to find paths from paper to code
        for paper_node in paper_nodes[:3]:
            for code_node in code_nodes[:3]:
                try:
                    path = nx.shortest_path(self.graph, paper_node, code_node)
                    path_with_edges = self._get_path_details(path)
                    paths_found.append(path_with_edges)
                    nodes_in_paths.update(path)
                    logger.info(f"      Found path: {' → '.join(path)}")
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue
        
        # If no direct paths, find related subgraph
        if not paths_found and (paper_nodes or code_nodes):
            seed_nodes = paper_nodes + code_nodes
            subgraph = self._get_neighborhood_subgraph(seed_nodes, hops=2)
            nodes_in_paths.update(subgraph['nodes'])
        
        return {
            'type': 'path',
            'paths': paths_found,
            'nodes': list(nodes_in_paths),
            'count': len(paths_found)
        }
    
    def _handle_dependency_query(self, query: str, entities: List[str]) -> Dict[str, Any]:
        """
        Handle dependency queries: "What does X depend on?"
        Uses reverse BFS (predecessors)
        """
        logger.info("   Running dependency analysis")
        
        target_nodes = self._find_nodes_by_entities(entities)
        
        dependencies = []
        all_dep_nodes = set()
        
        for node in target_nodes[:3]:
            # Get all predecessors (things this depends on)
            deps = list(self.graph.predecessors(node))
            
            # Get 2-hop dependencies
            for dep in deps[:5]:
                all_dep_nodes.add(node)
                all_dep_nodes.add(dep)
                
                edge_data = self.graph.edges[dep, node]
                dependencies.append({
                    'from': dep,
                    'to': node,
                    'relation': edge_data.get('relation', ''),
                    'description': edge_data.get('description', ''),
                    'from_name': self.graph.nodes[dep].get('name', dep),
                    'to_name': self.graph.nodes[node].get('name', node)
                })
                
                # 2nd hop
                for dep2 in list(self.graph.predecessors(dep))[:3]:
                    all_dep_nodes.add(dep2)
                    dependencies.append({
                        'from': dep2,
                        'to': dep,
                        'relation': self.graph.edges[dep2, dep].get('relation', ''),
                        'from_name': self.graph.nodes[dep2].get('name', dep2),
                        'to_name': self.graph.nodes[dep].get('name', dep)
                    })
        
        logger.info(f"      Found {len(dependencies)} dependencies")
        
        return {
            'type': 'dependency',
            'dependencies': dependencies,
            'nodes': list(all_dep_nodes),
            'count': len(dependencies)
        }
    
    def _handle_gap_query(self, query: str, entities: List[str]) -> Dict[str, Any]:
        """
        Handle gap analysis: "What's not implemented?"
        Finds unconnected nodes
        """
        logger.info("   Running gap analysis")
        
        gaps = []
        
        # Find paper nodes with no outgoing 'implements' edges
        for node, data in self.graph.nodes(data=True):
            if data.get('modality') == 'paper':
                # Check if has any outgoing cross-modal edges
                has_implementation = False
                for successor in self.graph.successors(node):
                    edge_data = self.graph.edges[node, successor]
                    if edge_data.get('cross_modal') and edge_data.get('relation') in ['implements', 'describes']:
                        has_implementation = True
                        break
                
                if not has_implementation:
                    gaps.append({
                        'node': node,
                        'name': data.get('name', ''),
                        'type': data.get('type', ''),
                        'description': data.get('description', ''),
                        'reason': 'No code implementation found'
                    })
        
        logger.info(f"      Found {len(gaps)} gaps")
        
        return {
            'type': 'gap',
            'gaps': gaps,
            'nodes': [g['node'] for g in gaps],
            'count': len(gaps)
        }
    
    def _handle_impact_query(self, query: str, entities: List[str]) -> Dict[str, Any]:
        """
        Handle impact analysis: "What's affected if I change X?"
        Uses forward BFS (successors)
        """
        logger.info("   💥 Running impact analysis")
        
        source_nodes = self._find_nodes_by_entities(entities)
        
        affected = []
        all_affected_nodes = set()
        
        for node in source_nodes[:3]:
            # Get all successors (things that depend on this)
            successors = list(self.graph.successors(node))
            
            # Get 2-hop impacts
            for succ in successors[:5]:
                all_affected_nodes.add(node)
                all_affected_nodes.add(succ)
                
                edge_data = self.graph.edges[node, succ]
                affected.append({
                    'from': node,
                    'to': succ,
                    'relation': edge_data.get('relation', ''),
                    'description': edge_data.get('description', ''),
                    'from_name': self.graph.nodes[node].get('name', node),
                    'to_name': self.graph.nodes[succ].get('name', succ),
                    'modality': self.graph.nodes[succ].get('modality', 'unknown')
                })
                
                # 2nd hop
                for succ2 in list(self.graph.successors(succ))[:3]:
                    all_affected_nodes.add(succ2)
                    affected.append({
                        'from': succ,
                        'to': succ2,
                        'relation': self.graph.edges[succ, succ2].get('relation', ''),
                        'from_name': self.graph.nodes[succ].get('name', succ),
                        'to_name': self.graph.nodes[succ2].get('name', succ2)
                    })
        
        logger.info(f"      Found {len(affected)} affected components")
        
        return {
            'type': 'impact',
            'affected': affected,
            'nodes': list(all_affected_nodes),
            'count': len(affected)
        }
    
    def _handle_summary_query(self, query: str, entities: List[str]) -> Dict[str, Any]:
        """
        Handle summary queries: "Summarize the architecture"
        Uses graph topology + centrality measures
        """
        logger.info("   📊 Running graph summarization")
        
        # Get central nodes (high degree)
        degree_centrality = nx.degree_centrality(self.graph)
        top_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Get betweenness centrality (bridge nodes)
        if self.graph.number_of_nodes() > 2:
            betweenness = nx.betweenness_centrality(self.graph)
            bridge_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]
        else:
            bridge_nodes = []
        
        # Build summary structure
        summary_nodes = set()
        key_concepts = []
        
        for node, centrality in top_nodes:
            summary_nodes.add(node)
            data = self.graph.nodes[node]
            key_concepts.append({
                'node': node,
                'name': data.get('name', ''),
                'type': data.get('type', ''),
                'modality': data.get('modality', ''),
                'centrality': centrality,
                'in_degree': self.graph.in_degree(node),
                'out_degree': self.graph.out_degree(node)
            })
        
        logger.info(f"      Identified {len(key_concepts)} key concepts")
        
        return {
            'type': 'summary',
            'key_concepts': key_concepts,
            'bridge_nodes': [n for n, _ in bridge_nodes],
            'nodes': list(summary_nodes),
            'graph_stats': {
                'total_nodes': self.graph.number_of_nodes(),
                'total_edges': self.graph.number_of_edges(),
                'paper_nodes': len([n for n, d in self.graph.nodes(data=True) if d.get('modality') == 'paper']),
                'code_nodes': len([n for n, d in self.graph.nodes(data=True) if d.get('modality') == 'code'])
            }
        }
    
    def _handle_find_query(self, query: str, entities: List[str]) -> Dict[str, Any]:
        """
        Handle find queries: "Where is X located?"
        Returns file paths and locations
        """
        logger.info("   📍 Running location finder")
        
        target_nodes = self._find_nodes_by_entities(entities)
        
        locations = []
        for node in target_nodes[:10]:
            data = self.graph.nodes[node]
            
            if data.get('modality') == 'code':
                locations.append({
                    'node': node,
                    'name': data.get('name', ''),
                    'files': data.get('files', []),
                    'functions': data.get('functions', []),
                    'type': data.get('type', '')
                })
            else:
                locations.append({
                    'node': node,
                    'name': data.get('name', ''),
                    'type': data.get('type', ''),
                    'description': data.get('description', '')[:200]
                })
        
        return {
            'type': 'find',
            'locations': locations,
            'nodes': target_nodes,
            'count': len(locations)
        }
    
    def _handle_related_query(self, query: str, entities: List[str]) -> Dict[str, Any]:
        """
        Handle related queries: "What's related to X?"
        Returns neighborhood subgraph
        """
        logger.info("   🌐 Running relationship finder")
        
        seed_nodes = self._find_nodes_by_entities(entities)
        
        if not seed_nodes:
            # No entities found, return central nodes
            degree_dict = dict(self.graph.degree())
            if degree_dict:
                sorted_nodes = sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)
                seed_nodes = [node for node, _ in sorted_nodes[:5]]
        
        subgraph = self._get_neighborhood_subgraph(seed_nodes, hops=2)
        
        return {
            'type': 'related',
            'nodes': subgraph['nodes'],
            'edges': subgraph['edges'],
            'count': len(subgraph['nodes'])
        }
    
    # Helper methods
    
    def _find_nodes_by_entities(self, entities: List[str], modality: str = None) -> List[str]:
        """Find graph nodes matching entity names"""
        matching_nodes = []
        
        for node, data in self.graph.nodes(data=True):
            if modality and data.get('modality') != modality:
                continue
            
            node_name = data.get('name', '').lower()
            for entity in entities:
                if entity.lower() in node_name or node_name in entity.lower():
                    matching_nodes.append(node)
                    break
        
        return matching_nodes
    
    def _get_path_details(self, path: List[str]) -> Dict[str, Any]:
        """Get detailed information about a path"""
        steps = []
        
        for i in range(len(path) - 1):
            source = path[i]
            target = path[i + 1]
            edge_data = self.graph.edges[source, target]
            
            steps.append({
                'from': source,
                'to': target,
                'from_name': self.graph.nodes[source].get('name', source),
                'to_name': self.graph.nodes[target].get('name', target),
                'relation': edge_data.get('relation', ''),
                'description': edge_data.get('description', '')
            })
        
        return {
            'nodes': path,
            'steps': steps,
            'length': len(path)
        }
    
    def _get_neighborhood_subgraph(self, seed_nodes: List[str], hops: int = 2) -> Dict[str, Any]:
        """Get neighborhood subgraph around seed nodes"""
        subgraph_nodes = set(seed_nodes)
        
        for _ in range(hops):
            new_nodes = set()
            for node in list(subgraph_nodes):
                if self.graph.has_node(node):
                    new_nodes.update(self.graph.neighbors(node))
                    new_nodes.update(self.graph.predecessors(node))
            subgraph_nodes.update(new_nodes)
            
            if len(subgraph_nodes) > 30:  # Limit size
                break
        
        # Get edges
        edges = []
        for source, target in self.graph.edges():
            if source in subgraph_nodes and target in subgraph_nodes:
                edges.append({
                    'source': source,
                    'target': target,
                    'relation': self.graph.edges[source, target].get('relation', '')
                })
        
        return {
            'nodes': list(subgraph_nodes),
            'edges': edges
        }
    
    def _enhance_with_llm(self, query: str, graph_evidence: Dict[str, Any]) -> str:
        """Use LLM to generate natural language answer from graph evidence"""
        
        # Build context from graph evidence
        context = self._build_context_from_evidence(graph_evidence)
        
        prompt = f"""You are a research paper + code analysis assistant. A user asked about a codebase and research paper.

USER QUESTION: {query}

GRAPH ANALYSIS RESULTS:
Query Type: {graph_evidence.get('type', 'unknown')}
{context}

YOUR TASK:
Generate a clear, helpful answer based on the graph analysis above.
- Reference specific concepts, algorithms, and code features by name
- Explain relationships and connections
- Use the graph structure to provide insights
- If paths exist, describe them step-by-step
- Be concise but informative

Answer:"""
        
        try:
            answer = self.llm._call_llm(prompt, max_tokens=500)
            return answer
        except Exception as e:
            logger.error(f"LLM enhancement failed: {e}")
            return self._generate_fallback_answer(graph_evidence)
    
    def _build_context_from_evidence(self, evidence: Dict[str, Any]) -> str:
        """Build context string from graph evidence"""
        lines = []
        
        if evidence.get('paths'):
            lines.append(f"\nPaths Found ({len(evidence['paths'])}):")
            for path in evidence['paths'][:3]:
                path_str = " → ".join([step['from_name'] for step in path['steps']] + [path['steps'][-1]['to_name']])
                lines.append(f"  • {path_str}")
        
        if evidence.get('dependencies'):
            lines.append(f"\nDependencies ({len(evidence['dependencies'])}):")
            for dep in evidence['dependencies'][:5]:
                lines.append(f"  • {dep['from_name']} --{dep['relation']}--> {dep['to_name']}")
        
        if evidence.get('gaps'):
            lines.append(f"\nGaps Found ({len(evidence['gaps'])}):")
            for gap in evidence['gaps'][:5]:
                lines.append(f"  • {gap['name']} ({gap['type']}): {gap['reason']}")
        
        if evidence.get('affected'):
            lines.append(f"\nAffected Components ({len(evidence['affected'])}):")
            for aff in evidence['affected'][:5]:
                lines.append(f"  • {aff['from_name']} impacts {aff['to_name']} ({aff['relation']})")
        
        if evidence.get('key_concepts'):
            lines.append(f"\nKey Concepts:")
            for concept in evidence['key_concepts'][:5]:
                lines.append(f"  • {concept['name']} ({concept['type']}, centrality: {concept['centrality']:.2f})")
        
        if evidence.get('locations'):
            lines.append(f"\nLocations:")
            for loc in evidence['locations'][:5]:
                if loc.get('files'):
                    lines.append(f"  • {loc['name']}: {', '.join(loc['files'][:2])}")
        
        return "\n".join(lines) if lines else "No specific graph evidence found."
    
    def _generate_fallback_answer(self, evidence: Dict[str, Any]) -> str:
        """Generate simple fallback answer if LLM fails"""
        etype = evidence.get('type', 'unknown')
        count = evidence.get('count', 0)
        
        return f"Found {count} {etype} results in the graph. Check the visualization for details."

