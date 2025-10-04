"""
LLM-First Paper Extractor - Context-aware extraction using code structure
Instead of parsing paper blindly, we use code context to extract relevant sections
"""

import json
from typing import Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class LLMPaperExtractor:
    """
    Smart paper extraction that uses code context to guide extraction.
    This is more intelligent than regex-based parsing.
    """
    
    def __init__(self, llm_analyzer):
        self.llm = llm_analyzer
    
    def extract_with_code_context(
        self, 
        paper_text: str, 
        code_features: List[Dict[str, Any]],
        max_paper_chars: int = 20000
    ) -> Dict[str, Any]:
        """
        Extract paper sections that are relevant to the given code features.
        This is a ONE-STEP process: extraction + mapping combined.
        
        Args:
            paper_text: Full paper text
            code_features: List of code features with names, descriptions, functions
            max_paper_chars: Max chars to send to LLM (for token limits)
        
        Returns:
            {
                'paper_nodes': [...],  # Relevant paper sections
                'cross_modal_edges': [...]  # Already mapped to code!
            }
        """
        logger.info("Using LLM-First Context-Aware Extraction...")
        
        # Truncate paper if too long
        paper_excerpt = paper_text[:max_paper_chars]
        if len(paper_text) > max_paper_chars:
            logger.warning(f"Paper truncated from {len(paper_text)} to {max_paper_chars} chars")
        
        # Build code context summary
        code_summary = self._build_code_summary(code_features)
        
        # LLM does BOTH extraction AND mapping in one shot
        result = self._llm_extract_and_map(paper_excerpt, code_summary, code_features)
        
        logger.info(f"Extracted {len(result['paper_nodes'])} relevant sections")
        logger.info(f"Created {len(result['cross_modal_edges'])} mappings")
        
        return result
    
    def _build_code_summary(self, code_features: List[Dict[str, Any]]) -> str:
        """Build concise code summary for LLM"""
        lines = ["# CODEBASE STRUCTURE:\n"]
        
        for feature in code_features[:15]:  # Limit to 15 features
            lines.append(f"\n## {feature['id']}: {feature['name']}")
            lines.append(f"Description: {feature['description']}")
            
            if feature.get('files'):
                lines.append(f"Files: {', '.join(feature['files'][:3])}")
            
            if feature.get('functions'):
                lines.append(f"Functions: {', '.join(feature['functions'][:8])}")
        
        return "\n".join(lines)
    
    def _llm_extract_and_map(
        self, 
        paper_text: str, 
        code_summary: str,
        code_features: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Single LLM call that:
        1. Reads the paper
        2. Creates a GRAPH of concepts with relationships
        3. Maps them to code features
        """
        
        prompt = f"""You are building a KNOWLEDGE GRAPH from a research paper and codebase.

# CODEBASE (what exists):
{code_summary}

# RESEARCH PAPER (build graph from):
{paper_text}

---

YOUR TASK - BUILD A RICH GRAPH STRUCTURE:

1. **Extract CONCEPT NODES** from the paper (methods, algorithms, components, techniques)
2. **Create EDGES between paper concepts** showing their relationships
3. **Map paper concepts to code features** where relevant

THINK GRAPH, NOT FLAT LIST! Show how concepts build on each other.

NODE TYPES:
- "concept" - Core ideas/methods (e.g., "Self-Attention")
- "algorithm" - Specific algorithms (e.g., "Scaled Dot-Product Attention")  
- "component" - System parts (e.g., "Encoder Layer")
- "technique" - Approaches (e.g., "Positional Encoding")

EDGE TYPES WITHIN PAPER:
- "builds_on" - Concept B builds on concept A
- "requires" - B requires A to work
- "extends" - B extends/improves A
- "uses" - B uses A as a component
- "enables" - A enables B
- "related_to" - Loose connection

EDGE TYPES PAPER→CODE:
- "implements" - Code implements paper concept
- "describes" - Paper describes code behavior
- "inspired_by" - Code inspired by paper

OUTPUT FORMAT (JSON):
{{
  "paper_nodes": [
    {{
      "id": "concept_attention",
      "type": "concept",
      "name": "Self-Attention Mechanism",
      "description": "Mechanism that relates positions in sequence to compute representation",
      "full_content": "Extracted text explaining this concept..."
    }},
    {{
      "id": "algo_scaled_dot_product",
      "type": "algorithm",
      "name": "Scaled Dot-Product Attention",
      "description": "Computes attention using queries, keys, values with scaling",
      "full_content": "Algorithm details..."
    }},
    {{
      "id": "component_encoder",
      "type": "component",
      "name": "Encoder Layer",
      "description": "Layer with self-attention and feed-forward network",
      "full_content": "Encoder details..."
    }}
  ],
  "paper_edges": [
    {{
      "source": "algo_scaled_dot_product",
      "target": "concept_attention",
      "type": "builds_on",
      "description": "Scaled dot-product is the core mechanism of self-attention"
    }},
    {{
      "source": "component_encoder",
      "target": "concept_attention",
      "type": "uses",
      "description": "Encoder layer uses self-attention as main component"
    }}
  ],
  "code_mappings": [
    {{
      "source": "concept_attention",
      "target": "feature_1",
      "type": "implements",
      "confidence": 95,
      "evidence": "feature_1 contains MultiHeadAttention class implementing paper concept",
      "description": "Attention mechanism from paper is implemented in code"
    }}
  ]
}}

CRITICAL:
- Extract 5-15 concept nodes (not just flat sections!)
- Create 8-20 edges BETWEEN paper nodes (show the graph structure!)
- Create 3-10 edges FROM paper TO code
- Focus on implementation-relevant concepts
- Show hierarchies, dependencies, and information flow

Return ONLY valid JSON:"""
        
        try:
            response = self.llm._call_llm(prompt, max_tokens=3000)
            
            # Extract JSON
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            result = json.loads(response.strip())
            
            # Validate structure
            paper_nodes = result.get('paper_nodes', [])
            paper_edges = result.get('paper_edges', [])
            code_mappings = result.get('code_mappings', result.get('mappings', []))
            
            # Ensure all node IDs are valid
            valid_node_ids = {node['id'] for node in paper_nodes}
            valid_feature_ids = {f['id'] for f in code_features}
            
            # Filter paper-to-paper edges
            filtered_paper_edges = []
            for edge in paper_edges:
                if edge['source'] in valid_node_ids and edge['target'] in valid_node_ids:
                    edge.setdefault('confidence', 80)
                    edge.setdefault('evidence', 'Paper analysis')
                    filtered_paper_edges.append(edge)
                else:
                    logger.warning(f"Skipping invalid paper edge: {edge}")
            
            # Filter paper-to-code mappings
            filtered_code_mappings = []
            for mapping in code_mappings:
                if mapping['source'] in valid_node_ids and mapping['target'] in valid_feature_ids:
                    # Ensure required fields
                    mapping.setdefault('confidence', 70)
                    mapping.setdefault('evidence', 'Semantic analysis')
                    mapping.setdefault('type', 'related')
                    filtered_code_mappings.append(mapping)
                else:
                    logger.warning(f"Skipping invalid code mapping: {mapping}")
            
            logger.info(f"Graph stats: {len(paper_nodes)} paper nodes, "
                       f"{len(filtered_paper_edges)} paper edges, "
                       f"{len(filtered_code_mappings)} cross-modal edges")
            
            return {
                'paper_nodes': paper_nodes,
                'paper_edges': filtered_paper_edges,  # NEW: edges within paper
                'cross_modal_edges': filtered_code_mappings
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ LLM returned invalid JSON: {e}")
            logger.error(f"Response: {response[:500]}")
            return {'paper_nodes': [], 'paper_edges': [], 'cross_modal_edges': []}
        
        except Exception as e:
            logger.error(f"❌ LLM extraction failed: {e}")
            return {'paper_nodes': [], 'paper_edges': [], 'cross_modal_edges': []}
    
    def extract_paper_text(self, file_path: str) -> str:
        """
        Extract raw text from paper (PDF or TXT).
        This is the ONLY parsing we do - just text extraction.
        """
        try:
            # Try PDF parsing
            text = self._extract_text_from_pdf(file_path)
            logger.info(f"Extracted {len(text)} chars from PDF")
            return text
        except:
            # Fallback: treat as text file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                logger.info(f"Read {len(text)} chars from text file")
                return text
            except Exception as e:
                logger.error(f"Failed to read paper: {e}")
                return ""
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages[:30]:  # First 30 pages
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            # Try pdfplumber
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text = ""
                    for page in pdf.pages[:30]:
                        text += page.extract_text() + "\n"
                    return text
            except ImportError:
                logger.warning("No PDF library available")
                raise

