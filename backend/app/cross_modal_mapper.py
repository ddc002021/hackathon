"""
Cross-Modal Mapper - Map paper concepts to code implementations
"""

import json
from typing import Dict, Any, List
from .llm_analyzer import LLMAnalyzer
import logging

logger = logging.getLogger(__name__)


class CrossModalMapper:
    """Map research paper concepts to code implementations"""
    
    def __init__(self, llm_analyzer: LLMAnalyzer):
        self.llm = llm_analyzer
    
    def map_paper_to_code(
        self, 
        paper_data: Dict[str, Any], 
        code_features: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create unified graph mapping paper concepts to code features
        
        Returns:
            {
                'paper_nodes': [...],
                'code_nodes': [...],
                'cross_modal_edges': [...]
            }
        """
        logger.info("Creating cross-modal mappings (Paper to Code)...")
        
        # Create paper nodes
        paper_nodes = self._create_paper_nodes(paper_data)
        
        # Map paper sections to code features
        mappings = self._llm_map_concepts(paper_data, code_features)
        
        logger.info(f"Created {len(paper_nodes)} paper nodes, {len(mappings)} mappings")
        
        return {
            'paper_nodes': paper_nodes,
            'code_nodes': code_features,
            'cross_modal_edges': mappings
        }
    
    def _create_paper_nodes(self, paper_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert paper sections into graph nodes"""
        nodes = []
        
        logger.info("=" * 80)
        logger.info("CREATING PAPER NODES:")
        logger.info("=" * 80)
        
        # Section nodes (no root node)
        for idx, section in enumerate(paper_data.get('sections', [])):
            # Use summary for description (short version)
            summary = section.get('summary', section['content'][:200])
            
            node = {
                'id': f'paper_section_{idx}',
                'type': 'paper_section',
                'name': section['title'],
                'description': summary,
                'full_content': section['content'],  # Full text for when clicked
                'modality': 'paper'
            }
            nodes.append(node)
            
            logger.info(f"\n  Node {idx}: {node['id']}")
            logger.info(f"    Title: {node['name']}")
            logger.info(f"    Description: {node['description'][:100]}...")
            logger.info(f"    Full Content Length: {len(node['full_content'])} chars")
        
        # Algorithm nodes
        for idx, algo in enumerate(paper_data.get('algorithms', [])):
            node = {
                'id': f'paper_algo_{idx}',
                'type': 'paper_algorithm',
                'name': algo['name'],
                'description': algo['description'][:200],
                'full_content': algo['description'],
                'modality': 'paper'
            }
            nodes.append(node)
            
            logger.info(f"\n  Algorithm {idx}: {node['id']}")
            logger.info(f"    Name: {node['name']}")
            logger.info(f"    Description: {node['description'][:100]}...")
        
        logger.info(f"\nCreated {len(nodes)} paper nodes total")
        logger.info("=" * 80)
        
        return nodes
    
    def _llm_map_concepts(
        self, 
        paper_data: Dict[str, Any], 
        code_features: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Use LLM to map paper concepts to code implementations"""
        
        if not paper_data.get('sections') or not code_features:
            return []
        
        # Build paper summary
        paper_summary = "PAPER SECTIONS:\n"
        for idx, section in enumerate(paper_data.get('sections', [])[:10]):
            summary = section.get('summary', section['content'][:200])
            paper_summary += f"\npaper_section_{idx}: {section['title']}\n"
            paper_summary += f"Summary: {summary}\n"
        
        # Add algorithms
        for idx, algo in enumerate(paper_data.get('algorithms', [])[:5]):
            paper_summary += f"\npaper_algo_{idx}: {algo['name']}\n"
            paper_summary += f"Description: {algo['description'][:200]}...\n"
        
        # Build code summary
        code_summary = "\nCODE FEATURES:\n"
        for feature in code_features[:10]:
            code_summary += f"\n{feature['id']}: {feature['name']}\n"
            code_summary += f"Description: {feature['description']}\n"
            code_summary += f"Files: {', '.join(feature['files'][:3])}\n"
            code_summary += f"Functions: {', '.join(feature['functions'][:5])}\n"
        
        prompt = f"""Analyze this research paper and codebase to find connections between paper concepts and code implementations.

{paper_summary}

{code_summary}

Your task: Identify which paper sections/algorithms are implemented by which code features.

For each mapping provide:
1. source: paper node ID (e.g., "paper_section_0" or "paper_algo_0")
2. target: code feature ID (e.g., "feature_0")
3. type: "implements" (code implements paper concept), "describes" (paper describes code), or "related" (loosely related)
4. confidence: 0-100 (how confident you are in this mapping)
5. evidence: What proves this connection
6. description: Human-readable explanation

Return ONLY a JSON array:
[
  {{
    "source": "paper_section_2",
    "target": "feature_1",
    "type": "implements",
    "confidence": 90,
    "evidence": "Section 2 describes attention mechanism, feature_1 implements attention.py",
    "description": "Attention mechanism from paper is implemented in code"
  }}
]

Return ONLY valid JSON:"""
        
        try:
            response = self.llm._call_llm(prompt, max_tokens=2000)
            
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            mappings = json.loads(response.strip())
            
            # Ensure all mappings have required fields
            for mapping in mappings:
                mapping.setdefault('confidence', 70)
                mapping.setdefault('evidence', 'Cross-modal analysis')
                mapping.setdefault('type', 'related')
            
            return mappings
            
        except Exception as e:
            logger.error(f"LLM mapping failed: {e}")
            return []

